SELECT s.П, p.Д
FROM S
CROSS JOIN P
WHERE (s.П, p.Д) NOT IN (
    SELECT П, Д
    FROM SPJ
)