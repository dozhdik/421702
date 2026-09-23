SELECT DISTINCT spj.ПР, spj.Д, spj.П
FROM SPJ
JOIN J AS j
ON spj.ПР = j.ПР
JOIN S AS s
ON spj.П = s.П
JOIN P AS p
ON spj.Д = p.Д
WHERE j.Город = s.Город AND s.Город = p.Город