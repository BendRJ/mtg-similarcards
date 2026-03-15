-- retrieves the number of distinct physical expansion sets released each year.
select substring(released_at,1,4) release_year, count(distinct code) sets
from "sets"
where set_type = 'expansion'
and digital is False
group by 1
order by 1 desc

-- retrieves all expansion sets released in 2026, ordered by release date.
select *
from "sets"
where set_type = 'expansion'
and substring(released_at,1,4) = '2026'
order by released_at