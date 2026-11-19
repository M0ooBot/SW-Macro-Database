-- @format 1
-- @block entries.create
CREATE VIRTUAL TABLE entries USING fts5(id UNINDEXED, title, answers, keywords, api, body, tokenize = 'unicode61');
-- @block gotchas.create
CREATE VIRTUAL TABLE gotchas USING fts5(number UNINDEXED, title, body, tokenize = 'unicode61');
-- @block entries.search
SELECT id FROM entries WHERE entries MATCH $q ORDER BY bm25(entries, 0, 8.0, 6.0, 4.0, 4.0, 1.0), id LIMIT $k;
-- @block gotchas.search
SELECT number FROM gotchas WHERE gotchas MATCH $q ORDER BY bm25(gotchas, 0, 8.0, 1.0), number LIMIT $k;
