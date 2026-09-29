-- Additive migration: existing checklist rows and quantities are not converted.
-- Copies are an atomic per-card aggregate with stable individual IDs.
alter table public.collection_items add column vault_copies jsonb;

create function public.validate_vault_copies(value jsonb) returns boolean
language plpgsql immutable security invoker set search_path = '' as $$
declare c jsonb; field text; limit_length integer; ids text[] := '{}';
begin
  if value is null then return true; end if;
  if jsonb_typeof(value) <> 'array' then return false; end if;
  if jsonb_array_length(value)>999 or pg_column_size(value)>4000000 then return false; end if;
  for c in select * from jsonb_array_elements(value) loop
    if jsonb_typeof(c)<>'object' or c->>'id' is null or c->>'id' !~ '^[A-Za-z0-9_-]{1,80}$' or (c->>'id')=any(ids) then return false; end if;
    ids:=array_append(ids,c->>'id');
    if coalesce(c->>'status','') not in ('owned','sold','traded') or coalesce(c->>'format','') not in ('raw','graded') or coalesce(c->>'currency','') !~ '^[A-Z]{3}$' then return false; end if;
    for field,limit_length in select * from (values ('parallel',120),('serialNumber',40),('gradingCompany',40),('grade',40),('certification',100),('condition',80),('seller',160),('location',160),('notes',2000)) as limits(field,lim) loop
      if coalesce(jsonb_typeof(c->field),'')<>'string' or length(c->>field)>limit_length then return false; end if;
    end loop;
    foreach field in array array['purchasePrice','estimatedValue','salePrice','saleFees'] loop
      if not (c ? field) then return false; end if;
      if c->field <> 'null'::jsonb then
        if jsonb_typeof(c->field)<>'number' then return false; end if;
        if (c->>field)::numeric<0 or (c->>field)::numeric>9999999999.99 then return false; end if;
      end if;
    end loop;
    foreach field in array array['acquiredAt','soldAt','valuedAt'] loop
      if coalesce(c->>field,'')<>'' then
        if c->>field !~ '^\d{4}-\d{2}-\d{2}$' then return false; end if;
        perform (c->>field)::date;
      end if;
    end loop;
    if c->>'format'='graded' and (btrim(c->>'gradingCompany')='' or btrim(c->>'grade')='') then return false; end if;
    if c->>'status'='sold' and (c->'salePrice'='null'::jsonb or coalesce(c->>'soldAt','')='') then return false; end if;
    if coalesce(c->>'soldAt','')<>'' and coalesce(c->>'acquiredAt','')<>'' and (c->>'soldAt')::date < (c->>'acquiredAt')::date then return false; end if;
    foreach field in array array['front','back'] loop
      if c->>field is not null and c->>field !~ '^[a-f0-9-]{36}/[A-Za-z0-9_-]+\.jpg$' then return false; end if;
    end loop;
  end loop;
  return true;
exception when others then return false;
end $$;
revoke all on function public.validate_vault_copies(jsonb) from public,anon;
grant execute on function public.validate_vault_copies(jsonb) to authenticated;
alter table public.collection_items add constraint collection_vault_valid check(public.validate_vault_copies(vault_copies));

create function public.protect_vault_aggregate() returns trigger
language plpgsql security invoker set search_path = '' as $$
declare owned_count integer;
begin
  if TG_OP='DELETE' then
    if current_user='authenticated' and OLD.vault_copies is not null then
      raise exception 'Remove individual copies through the Vault to preserve sale history';
    end if;
    return OLD;
  end if;
  if TG_OP='UPDATE' and OLD.vault_copies is not null and NEW.vault_copies is null then
    raise exception 'Vault records cannot be replaced by a legacy checklist update';
  end if;
  if NEW.vault_copies is not null then
    if not public.validate_vault_copies(NEW.vault_copies) then raise exception 'Invalid Vault copy records'; end if;
    select count(*) into owned_count from jsonb_array_elements(NEW.vault_copies) c where c->>'status'='owned';
    NEW.quantity:=greatest(1,owned_count);
    if owned_count>0 then NEW.status:='owned'; end if;
    -- Archived-only rows remain as history; the UI derives missing from copies.
  end if;
  return NEW;
end $$;
revoke all on function public.protect_vault_aggregate() from public,anon,authenticated;
create trigger protect_vault_aggregate before insert or update or delete on public.collection_items
for each row execute function public.protect_vault_aggregate();

insert into storage.buckets(id,name,public,file_size_limit,allowed_mime_types)
values('vault-photos','vault-photos',false,5242880,array['image/jpeg']);
create policy "Vault owners read photos" on storage.objects for select to authenticated
using(bucket_id='vault-photos' and (storage.foldername(name))[1]=(select auth.uid())::text);
create policy "Vault owners upload photos" on storage.objects for insert to authenticated
with check(bucket_id='vault-photos' and (storage.foldername(name))[1]=(select auth.uid())::text);
create policy "Vault owners delete photos" on storage.objects for delete to authenticated
using(bucket_id='vault-photos' and (storage.foldername(name))[1]=(select auth.uid())::text);

comment on column public.collection_items.vault_copies is 'Private physical-copy records. Null means legacy checklist mode. Empty array means no physical copies; archived records use sold/traded status. Costs and valuations are user-entered, not market data.';
