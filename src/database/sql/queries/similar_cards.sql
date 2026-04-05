SELECT c.name, c.type_line, c.oracle_text,
       c.embedding <=> (SELECT embedding FROM cards WHERE id = %(card_id)s) AS distance
FROM cards c
WHERE c.embedding IS NOT NULL
  AND c.id != %(card_id)s
ORDER BY distance
LIMIT %(limit)s;
