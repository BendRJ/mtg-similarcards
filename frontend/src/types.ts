// Mirrors src/app/backend/models.py. Dates arrive as ISO strings.

export interface CardSummary {
  id: string;
  name: string;
  mana_cost: string | null;
  type_line: string | null;
  colors: string[] | null;
  rarity: string | null;
  set_code: string | null;
  image_url: string | null;
}

export interface AutocompleteCard extends CardSummary {
  image_url_small: string | null;
}

export interface CardDetail extends CardSummary {
  oracle_id: string | null;
  cmc: number | null;
  oracle_text: string | null;
  flavor_text: string | null;
  power: string | null;
  toughness: string | null;
  loyalty: string | null;
  keywords: string[] | null;
  color_identity: string[] | null;
  set_name: string | null;
  collector_number: string | null;
  released_at: string | null;
  artist: string | null;
  legalities: Record<string, string> | null;
  image_url_large: string | null;
}

export interface Printing {
  id: string;
  set_code: string | null;
  set_name: string | null;
  collector_number: string | null;
  released_at: string | null;
  rarity: string | null;
  image_url: string | null;
}

export interface SimilarCard extends CardSummary {
  distance: number;
}

export interface SetSummary {
  code: string;
  name: string;
  released_at: string | null;
  set_type: string | null;
  card_count: number | null;
  icon_svg_uri: string | null;
}

export interface SearchFilter {
  field: "oracle_text" | "name" | "keywords" | "type" | "colors";
  op: string;
  value: string | string[];
}

export interface SearchRequest {
  filters: SearchFilter[];
  sort: "name" | "cmc_asc" | "cmc_desc";
}

export interface SearchResponse {
  // total is the full match count, cards holds at most 200.
  total: number;
  cards: CardSummary[];
}
