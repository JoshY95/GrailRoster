-- Proposed, NOT applied. Official WWE NOW #107–112; baseline verified on 2026-10-24.
-- One-time guarded data-only addition. Preserve every existing card id, ownership row and variant.
begin;
do $$
begin
 if (select card_count from public.catalogue_sets where id='2026-topps-now-wwe') <> 126
 or (select count(*) from public.catalogue_cards where set_id='2026-topps-now-wwe') <> 126
 or (select count(*) from public.catalogue_variants where set_id='2026-topps-now-wwe') <> 126
 or exists (select 1 from public.catalogue_cards where id in ('2026-TNWWE-BASE-107','2026-TNWWE-BASE-108','2026-TNWWE-BASE-109','2026-TNWWE-BASE-110','2026-TNWWE-BASE-111','2026-TNWWE-BASE-112'))
 then raise exception 'Topps NOW baseline changed; review before import';
 end if;
end $$;
-- Shift legacy poster/HOF card order out of the way without touching card identities.
update public.catalogue_cards set checklist_order=checklist_order+1000 where set_id='2026-topps-now-wwe' and checklist_order>106;
update public.catalogue_variants set variant_order=variant_order+1000 where set_id='2026-topps-now-wwe' and variant_order>106;
update public.catalogue_cards set checklist_order=checklist_order-994 where set_id='2026-topps-now-wwe' and checklist_order>1106;
update public.catalogue_variants set variant_order=variant_order-994 where set_id='2026-topps-now-wwe' and variant_order>1106;
insert into public.catalogue_cards
(id,set_id,checklist_order,category,subset_code,card_number,display_name,subject_1,subject_2,roster,rookie,parallel_group,image_status,pricing_status,source_url,notes)
values
('2026-TNWWE-BASE-107','2026-topps-now-wwe',107,'Base','BASE','107','Alexa Bliss / Tatum Paxley','Alexa Bliss','Tatum Paxley',null,false,'BASE','Missing','Unpriced','https://www.topps.com/products/alexa-bliss-and-tatum-paxley-2026-wwe-topps-now-r-card-107','Topps product listing; available 2026-10-12; base print run 2179. Gold /50, Orange /25, Black /10, Red /5 and FoilFractor 1/1. Open-Edition Base Card Foil Parallels Numbered to /50 and lower. Parallels: /50 Gold Foil; /25 Orange Foil; /10 Black Foil; /5 Red Foil; /1 FoilFractor. Look for: /1 Dual Autograph Redemption Card Conditional Chrome tiers not assigned.'),
('2026-TNWWE-BASE-108','2026-topps-now-wwe',108,'Base','BASE','108','Tiffany Stratton','Tiffany Stratton',null,null,false,'BASE','Missing','Unpriced','https://www.topps.com/products/tiffany-stratton-2026-wwe-topps-now-r-card-108','Topps product listing; available 2026-10-12; base print run 2018. Gold /50, Orange /25, Black /10, Red /5 and FoilFractor 1/1. Open-Edition Base Card Foil Parallels Numbered to /50 and lower. Parallels: /50 Gold Foil; /25 Orange Foil; /10 Black Foil; /5 Red Foil; /1 FoilFractor. Look for: /5 and /1 Autograph Redemption Cards Conditional Chrome tiers not assigned.'),
('2026-TNWWE-BASE-109','2026-topps-now-wwe',109,'Base','BASE','109','Liv Morgan','Liv Morgan',null,null,false,'BASE','Missing','Unpriced','https://www.topps.com/products/liv-morgan-2026-wwe-topps-now-r-card-109','Topps product listing; available 2026-10-12; base print run 1985. Gold /50, Orange /25, Black /10, Red /5 and FoilFractor 1/1. Open-Edition Base Card Foil Parallels Numbered to /50 and lower. Parallels: /50 Gold Foil; /25 Orange Foil; /10 Black Foil; /5 Red Foil; /1 FoilFractor. Look for: /5 and /1 Autograph Redemption Cards Conditional Chrome tiers not assigned.'),
('2026-TNWWE-BASE-110','2026-topps-now-wwe',110,'Base','BASE','110','Je''Von Evans','Je''Von Evans',null,null,false,'BASE','Missing','Unpriced','https://www.topps.com/products/je-von-evans-2026-wwe-topps-now-r-card-110','Topps product listing; available 2026-10-12; base print run 820. Gold /50, Orange /25, Black /10, Red /5 and FoilFractor 1/1. No autograph announced. Conditional Chrome tiers not assigned.'),
('2026-TNWWE-BASE-111','2026-topps-now-wwe',111,'Base','BASE','111','Penta','Penta',null,null,false,'BASE','Missing','Unpriced','https://www.topps.com/products/penta-2026-wwe-topps-now-r-card-111','Topps product listing; available 2026-10-12; base print run 4256. Gold /50, Orange /25, Black /10, Red /5 and FoilFractor 1/1. Open-Edition Base Card Foil Parallels Numbered to /50 and lower. Parallels: /50 Gold Foil; /25 Orange Foil; /10 Black Foil; /5 Red Foil; /1 FoilFractor. Look for: /5 and /1 Autograph Redemption Cards Conditional Chrome tiers not assigned.'),
('2026-TNWWE-BASE-112','2026-topps-now-wwe',112,'Base','BASE','112','946','946',null,null,false,'BASE','Missing','Unpriced','https://www.topps.com/products/946-2026-wwe-topps-now-r-card-112','Topps product listing; available 2026-10-13; base print run 597. Gold /50, Orange /25, Black /10, Red /5 and FoilFractor 1/1. No autograph announced. Conditional Chrome tiers not assigned.');
insert into public.catalogue_variants
(id,set_id,card_id,variant_order,subset,card_number,display_name,parallel,serial_cap,serial_exact,exclusive_note,numbering_note,verification_status)
values
('2026-TNWWE-BASE-107-IDENTITY','2026-topps-now-wwe','2026-TNWWE-BASE-107',107,'Regular','107','Alexa Bliss / Tatum Paxley','Checklist identity',null,null,null,'Unnumbered checklist identity; base print run is not a serial cap.','Official Topps product listing'),
('2026-TNWWE-BASE-108-IDENTITY','2026-topps-now-wwe','2026-TNWWE-BASE-108',108,'Regular','108','Tiffany Stratton','Checklist identity',null,null,null,'Unnumbered checklist identity; base print run is not a serial cap.','Official Topps product listing'),
('2026-TNWWE-BASE-109-IDENTITY','2026-topps-now-wwe','2026-TNWWE-BASE-109',109,'Regular','109','Liv Morgan','Checklist identity',null,null,null,'Unnumbered checklist identity; base print run is not a serial cap.','Official Topps product listing'),
('2026-TNWWE-BASE-110-IDENTITY','2026-topps-now-wwe','2026-TNWWE-BASE-110',110,'Regular','110','Je''Von Evans','Checklist identity',null,null,null,'Unnumbered checklist identity; base print run is not a serial cap.','Official Topps product listing'),
('2026-TNWWE-BASE-111-IDENTITY','2026-topps-now-wwe','2026-TNWWE-BASE-111',111,'Regular','111','Penta','Checklist identity',null,null,null,'Unnumbered checklist identity; base print run is not a serial cap.','Official Topps product listing'),
('2026-TNWWE-BASE-112-IDENTITY','2026-topps-now-wwe','2026-TNWWE-BASE-112',112,'Regular','112','946','Checklist identity',null,null,null,'Unnumbered checklist identity; base print run is not a serial cap.','Official Topps product listing');
update public.catalogue_subsets set card_count=112 where set_id='2026-topps-now-wwe' and subset_code='BASE' and card_count=106;
update public.catalogue_sets set card_count=132,variant_count=132,updated_at=now() where id='2026-topps-now-wwe' and card_count=126;
do $$
begin
 if (select count(*) from public.catalogue_cards where set_id='2026-topps-now-wwe')<>132
 or (select count(*) from public.catalogue_variants where set_id='2026-topps-now-wwe')<>132
 or (select count(distinct checklist_order) from public.catalogue_cards where set_id='2026-topps-now-wwe')<>132
 or (select count(distinct variant_order) from public.catalogue_variants where set_id='2026-topps-now-wwe')<>132
 or (select card_count from public.catalogue_sets where id='2026-topps-now-wwe')<>132
 or exists (select 1 from public.catalogue_variants v left join public.catalogue_cards c on c.id=v.card_id where v.set_id='2026-topps-now-wwe' and c.id is null)
 then raise exception 'Topps NOW import validation failed';
 end if;
end $$;
commit;
