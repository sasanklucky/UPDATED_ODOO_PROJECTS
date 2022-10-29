Function: public.agg_data(date, date, text, integer)

DROP FUNCTION public.agg_data(date, date, text, integer);

drop type if exists agg_table cascade;
create type agg_table as
          (resource_id int,
          resource_name varchar,
	  check_in timestamp,
	  check_out timestamp);


CREATE OR REPLACE FUNCTION public.agg_data(
    stdate date,
    enddate date,
    resources text,
    company_id integer)
  RETURNS SETOF agg_table AS
$BODY$
DECLARE
	r agg_table%rowtype;
	rec record;
	ids INT[];
	i int;


BEGIN
    ids = string_to_array($3,',');

    DROP TABLE if exists tmp_table;
    CREATE TEMP TABLE tmp_table
	( resource_id int,
	  resource_name varchar,
	  check_in timestamp,
	  check_out timestamp
	)
     ON COMMIT DROP;

    FOREACH i IN array ids  loop
        insert into tmp_table(resource_id, resource_name, check_in, check_out)
        with c as
	  ( select start_datetime, end_datetime, r.name as resource_name1, resource_name, max(end_datetime) over (order by start_datetime
					  rows between unbounded preceding
						   and 1 preceding)
			as previous_max
			from  account_analytic_line a
			    inner join resource_resource r
			    on r.id = a.resource_name

			    inner join project_task k on k.id = a.task_id
			    inner join sale_order_line sl on sl.id = k.sale_line_id

			    where a.entry_type = 'actual'
			    and a.status in (SELECT id from task_status WHERE name in ('Start','Restart'))
			    and (to_char((a.start_datetime ::TIMESTAMP::VARCHAR || ' UTC')::TIMESTAMPTZ AT TIME ZONE 'Asia/kolkata', 'yyyy-mm-dd')::date
			    between $1  and $2
			    or
			     to_char((a.end_datetime ::TIMESTAMP::VARCHAR || ' UTC')::TIMESTAMPTZ AT TIME ZONE 'Asia/kolkata', 'yyyy-mm-dd')::date
			    between $1  and $2)

			    and r.company_id = $4
			    and r.id = i
		  )
		select resource_name,resource_name1, start_datetime ,
		       coalesce(lead(previous_max) over (order by start_datetime),
				(select max(end_datetime) from  account_analytic_line a
				    inner join resource_resource r
				    on r.id = a.resource_name

			    inner join project_task k on k.id = a.task_id
			    inner join sale_order_line sl on sl.id = k.sale_line_id

			    where a.entry_type = 'actual'
			    and a.status in (SELECT id from task_status WHERE name in ('Start','Restart'))
			    --and ac.dayofweek = extract(dow from '2018-02-13'::date)::char
			    and (to_char((a.start_datetime ::TIMESTAMP::VARCHAR || ' UTC')::TIMESTAMPTZ AT TIME ZONE 'Asia/kolkata', 'yyyy-mm-dd')::date
			    between $1  and $2
			     or
			     to_char((a.end_datetime ::TIMESTAMP::VARCHAR || ' UTC')::TIMESTAMPTZ AT TIME ZONE 'Asia/kolkata', 'yyyy-mm-dd')::date
			    between $1  and $2)

			    and r.company_id = $4
			    and r.id = i)
		       ) as end_date
	from c
	where previous_max < start_datetime
	   or previous_max is null ;

    end loop;


    for r in select * from  tmp_table loop
	return next r;
    end loop;

    --return ;
END

$BODY$
  LANGUAGE plpgsql VOLATILE
  COST 100
  ROWS 1000;
ALTER FUNCTION public.agg_data(date, date, text, integer)
  OWNER TO wms;