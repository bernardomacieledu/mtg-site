-- Schema das tabelas legadas (models com managed = False no Django).
-- Executado automaticamente pelo MySQL no primeiro boot do volume.

CREATE DATABASE IF NOT EXISTS mtg_db
  CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;

USE mtg_db;

CREATE TABLE IF NOT EXISTS cards (
  scryfall_id      VARCHAR(36)  NOT NULL,
  name             VARCHAR(255) NULL,
  mana_cost        VARCHAR(50)  NULL,
  cmc              DECIMAL(5,1) NULL,
  type_line        VARCHAR(255) NULL,
  oracle_text      TEXT         NULL,
  rarity           VARCHAR(20)  NULL,
  image_url_normal VARCHAR(512) NULL,
  local_image_path VARCHAR(512) NULL,
  set_code         VARCHAR(10)  NULL,
  release_date     DATE         NULL,
  lang             VARCHAR(10)  NULL,
  PRIMARY KEY (scryfall_id),
  KEY idx_cards_name         (name),
  KEY idx_cards_set          (set_code),
  KEY idx_cards_release      (release_date),
  KEY idx_cards_rarity       (rarity),
  KEY idx_cards_name_release (name, release_date)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS rules (
  id          INT AUTO_INCREMENT NOT NULL,
  rule_number VARCHAR(20) NOT NULL,
  rule_text   TEXT        NOT NULL,
  chapter_id  VARCHAR(10) NULL,
  PRIMARY KEY (id),
  UNIQUE KEY uniq_rule_number (rule_number),
  KEY idx_rules_chapter (chapter_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
