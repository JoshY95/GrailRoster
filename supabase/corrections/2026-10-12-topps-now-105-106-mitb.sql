-- Applied to Sydney on 2026-10-12. Historical, guarded one-time catalogue addition.
-- Re-running is intentionally blocked by the baseline check.
begin;
do $$
begin
 if (select card_count from public.catalogue_sets where id='2026-topps-now-wwe') <> 123
 or (select count(*) from public.catalogue_cards where set_id='2026-topps-now-wwe') <> 123
 or (select count(*) from public.catalogue_variants where set_id='2026-topps-now-wwe') <> 123
 or exists (select 1 from public.catalogue_cards where id in ('2026-TNWWE-BASE-105','2026-TNWWE-BASE-106','2026-TNWWE-POSTER-MITB'))
 then raise exception 'Topps NOW baseline changed; review before import';
 end if;
end $$;
update public.catalogue_cards set checklist_order=checklist_order+1000
where set_id='2026-topps-now-wwe' and checklist_order>104;
update public.catalogue_variants set variant_order=variant_order+1000
where set_id='2026-topps-now-wwe' and variant_order>104;
update public.catalogue_cards set checklist_order=case when checklist_order between 1105 and 1113 then checklist_order-998 else checklist_order-997 end
where set_id='2026-topps-now-wwe' and checklist_order>1104;
update public.catalogue_variants set variant_order=case when variant_order between 1105 and 1113 then variant_order-998 else variant_order-997 end
where set_id='2026-topps-now-wwe' and variant_order>1104;
insert into public.catalogue_cards
(id,set_id,checklist_order,category,subset_code,card_number,display_name,subject_1,subject_2,roster,rookie,parallel_group,image_status,pricing_status,source_url,notes)
values
('2026-TNWWE-BASE-105','2026-topps-now-wwe',105,'Base','BASE','105','Blake Monroe','Blake Monroe',null,null,false,'BASE','Missing','Unpriced','https://www.topps.com/products/blake-monroe-2026-wwe-topps-now%C2%AE-card-105','Topps product listing; available 2026-10-05; base print run: 1626. Explicit foil parallels /50, /25, /10, /5 and /1. Conditional Chrome tiers not assigned.'),
('2026-TNWWE-BASE-106','2026-topps-now-wwe',106,'Base','BASE','106','Wren Sinclair','Wren Sinclair',null,null,false,'BASE','Missing','Unpriced','https://fr.topps.com/products/wren-sinclair-2026-wwe-topps-now%C2%AE-card-106','Topps product listing; available 2026-10-07; base print run not yet published. Explicit foil parallels /50, /25, /10, /5 and /1. Conditional Chrome tiers not assigned.'),
('2026-TNWWE-POSTER-MITB','2026-topps-now-wwe',116,'Base','POSTER','MITB','Punk/Penta/Tiff/Trick/Sol','Punk/Penta/Tiff/Trick/Sol',null,null,false,'POSTER','Missing','Unpriced','https://www.topps.com/products/punk-penta-tiff-trick-sol-2026-wwe-topps-now%C2%AE-card-mitb','Topps product listing; available 2026-10-09; base print run not yet published. MITB Poster Rainbow Foil Short Print and Gold Super Short Print /26 are explicitly confirmed. Product title retained verbatim; subject metadata does not list Sol.');
insert into public.catalogue_variants
(id,set_id,card_id,variant_order,subset,card_number,display_name,parallel,serial_cap,serial_exact,exclusive_note,numbering_note,verification_status)
values
('2026-TNWWE-BASE-105-IDENTITY','2026-topps-now-wwe','2026-TNWWE-BASE-105',105,'Regular','105','Blake Monroe','Checklist identity',null,null,null,'Unnumbered checklist identity; base print run is not a serial cap.','Official Topps product listing'),
('2026-TNWWE-BASE-106-IDENTITY','2026-topps-now-wwe','2026-TNWWE-BASE-106',106,'Regular','106','Wren Sinclair','Checklist identity',null,null,null,'Unnumbered checklist identity; base print run is not a serial cap.','Official Topps product listing'),
('2026-TNWWE-POSTER-MITB-IDENTITY','2026-topps-now-wwe','2026-TNWWE-POSTER-MITB',116,'Event poster','MITB','Punk/Penta/Tiff/Trick/Sol','Checklist identity',null,null,null,'Unnumbered checklist identity; base print run is not a serial cap.','Official Topps product listing');
update public.catalogue_subsets set card_count=case subset_code when 'BASE' then 106 when 'POSTER' then 14 else card_count end where set_id='2026-topps-now-wwe' and subset_code in ('BASE','POSTER');
update public.catalogue_sets set card_count=126,variant_count=126,updated_at=now() where id='2026-topps-now-wwe';
do $$
begin
 if (select count(*) from public.catalogue_cards where set_id='2026-topps-now-wwe')<>126
 or (select count(*) from public.catalogue_variants where set_id='2026-topps-now-wwe')<>126
 or (select count(distinct checklist_order) from public.catalogue_cards where set_id='2026-topps-now-wwe')<>126
 or exists (select 1 from public.catalogue_variants v left join public.catalogue_cards c on c.id=v.card_id where v.set_id='2026-topps-now-wwe' and c.id is null)
 then raise exception 'Topps NOW import validation failed';
 end if;
end $$;
commit;
