-- Витрина experiment_summary: одна строка на эксперимент, всё для решения по доле завершивших.
-- Бутстреп-интервал и p-value z-теста приходят из Python в таблице effect_stats, номер исключённого эксперимента -
-- в переменной excluded. Правило решений зафиксировано в ноутбуке 02, порог +3 п.п.

create or replace table experiment_summary as
with sizes as (
    select
        experiment_id,
        any_value(experiment_name) as experiment_name,
        count(*) filter (where grp = 'C') as n_c,
        count(*) filter (where grp = 'E') as n_e,
        avg(complete) filter (where grp = 'C') as rate_c,
        avg(complete) filter (where grp = 'E') as rate_e
    from exp_students
    group by all
),
-- BH только по экспериментам, которые входят в решения
ranked as (
    select experiment_id, p, row_number() over (order by p) as k, count(*) over () as m
    from effect_stats
    where experiment_id <> getvariable('excluded')
),
bh as (
    select
        experiment_id,
        least(1, min(p * m / k) over (order by k desc rows between unbounded preceding and current row)) as p_bh
    from ranked
),
base as (
    select
        s.*,
        s.rate_e - s.rate_c as effect,
        e.boot_lo as ci_lo,
        e.boot_hi as ci_hi,
        e.p,
        bh.p_bh,
        -- MDE при alpha = 0,05 и мощности 0,8: 1,959964 + 0,841621 = 2,801585
        2.801585 * sqrt(s.rate_c * (1 - s.rate_c) * (1 / s.n_c + 1 / s.n_e)) as mde,
        e.sens_boot_hi
    from sizes s
    join effect_stats e using (experiment_id)
    left join bh using (experiment_id)
),
ruled as (
    select
        *,
        case
            when experiment_id = getvariable('excluded') then 'исключён'
            when p_bh < 0.05 and effect > 0 then 'выкатывать'
            when p_bh < 0.05 then 'не выкатывать'
            when ci_hi < 0.03 then 'не выкатывать'
            else 'мало данных'
        end as rule_decision
    from base
)
select
    experiment_id,
    experiment_name,
    n_c,
    n_e,
    rate_c,
    rate_e,
    effect,
    ci_lo,
    ci_hi,
    p,
    p_bh,
    mde,
    -- 256027: если с недостающими бросившими в C решение другое, пишем «мало данных»
    case
        when sens_boot_hi is not null
            and rule_decision <> (case when sens_boot_hi < 0.03 then 'не выкатывать' else 'мало данных' end)
            then 'мало данных'
        else rule_decision
    end as decision,
    coalesce(notes.note, '') as note
from ruled
left join (values
    (237447, 'контроль 98,5%: расти некуда; интервал ниже нуля, но после BH незначимо'),
    (256027, 'в E 6 рано бросивших без пары в C; с ними в C интервал до +7,0 п.п.'),
    (263057, 'группы несравнимы: в контроле, похоже, нет рано бросивших'),
    (293151, 'гипотеза для повторного теста: среди увидевших условие +8,4 п.п., после BH 0,49'),
    (377658, 'контроль 97%: +3 п.п. невозможны')
) as notes(experiment_id, note) using (experiment_id)
order by experiment_id;
