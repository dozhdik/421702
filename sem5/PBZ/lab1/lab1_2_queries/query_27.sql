SELECT DISTINCT s1.П
FROM SPJ AS s1
WHERE s1.Д = 'Д1' AND s1.S > (
    SELECT AVG(s2.S)
    FROM SPJ AS s2
    WHERE s2.Д = 'Д1' AND s2.ПР = s1.ПР
)