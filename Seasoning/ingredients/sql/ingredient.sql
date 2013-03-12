SET @OLD_SQL_NOTES=@@SQL_NOTES, SQL_NOTES=0;
SET FOREIGN_KEY_CHECKS=0;

-- ---
-- Table 'Ingredient'
-- 
-- ---

DROP TABLE IF EXISTS `ingredient`;
		
CREATE TABLE `ingredient` (
  `id` INT UNSIGNED NULL AUTO_INCREMENT DEFAULT NULL,
  `type` VARCHAR(10) NOT NULL,
  `category` VARCHAR(2) NOT NULL,
  `veganism` VARCHAR(2) NOT NULL,
  `description` TEXT NULL,
  `conservation_tip` TEXT,
  `preparation_tip` TEXT NULL,
  `properties` TEXT NULL,
  `source` TEXT NULL,
  `base_footprint` FLOAT NOT NULL DEFAULT 0,
  `image` VARCHAR(100) NOT NULL DEFAULT 'images/ingredients/no_image.png',
  `accepted` BINARY NOT NULL DEFAULT '0',
  PRIMARY KEY (`id`)
);


-- ---
-- Table 'Synonym'
-- 
-- ---

DROP TABLE IF EXISTS `synonym`;
		
CREATE TABLE `synonym` (
  `id` INT UNSIGNED NULL AUTO_INCREMENT DEFAULT NULL,
  `name` VARCHAR(50) NOT NULL,
  `plural_name` VARCHAR(50) DEFAULT NULL,
  `ingredient` INT UNSIGNED NULL DEFAULT 0,
  PRIMARY KEY (`id`)
);

ALTER TABLE `synonym` ADD FOREIGN KEY (ingredient) REFERENCES `ingredient` (`id`)
    ON UPDATE CASCADE ON DELETE CASCADE;


-- ---
-- Table 'Unit'
-- 
-- ---

DROP TABLE IF EXISTS `unit`;
		
CREATE TABLE `unit` (
  `id` INT UNSIGNED NULL AUTO_INCREMENT DEFAULT NULL,
  `name` VARCHAR(30) NOT NULL DEFAULT 'NULL',
  `short_name` VARCHAR(10) NOT NULL DEFAULT 'NULL',
  PRIMARY KEY (`id`)
);

-- ---
-- Table 'CanUseUnit'
-- 
-- ---

DROP TABLE IF EXISTS `canuseunit`;
		
CREATE TABLE `canuseunit` (
  `id` INT UNSIGNED NULL AUTO_INCREMENT DEFAULT NULL,
  `ingredient` INT UNSIGNED NOT NULL,
  `unit` INT UNSIGNED NOT NULL,
  `conversion_factor` FLOAT NOT NULL DEFAULT 1,
  PRIMARY KEY (`id`)
);

ALTER TABLE `canuseunit` ADD FOREIGN KEY (ingredient) REFERENCES `ingredient` (`id`)
    ON UPDATE CASCADE ON DELETE CASCADE;
ALTER TABLE `canuseunit` ADD FOREIGN KEY (unit) REFERENCES `unit` (`id`)
    ON UPDATE CASCADE ON DELETE CASCADE;


-- ---
-- Table 'VegetalIngredient'
-- 
-- ---

DROP TABLE IF EXISTS `vegetalingredient`;
		
CREATE TABLE `vegetalingredient` (
  `ingredient` INT UNSIGNED NULL DEFAULT NULL,
  `preservability` INT UNSIGNED NOT NULL DEFAULT 0,
  `preservation_footprint` FLOAT NOT NULL DEFAULT 0,
  PRIMARY KEY (`ingredient`)
);

ALTER TABLE `vegetalingredient` ADD FOREIGN KEY (ingredient) REFERENCES `ingredient` (`id`)
    ON UPDATE CASCADE ON DELETE CASCADE;


-- ---
-- Table 'Country'
-- 
-- ---

DROP TABLE IF EXISTS `country`;
		
CREATE TABLE `country` (
  `id` INT UNSIGNED NULL AUTO_INCREMENT DEFAULT NULL,
  `name` VARCHAR(50) NOT NULL,
  `distance` INT UNSIGNED NOT NULL DEFAULT 0,
  PRIMARY KEY (`id`)
);

-- ---
-- Table 'TransportMethod'
-- 
-- ---

DROP TABLE IF EXISTS `transportmethod`;
		
CREATE TABLE `transportmethod` (
  `id` INT UNSIGNED NULL AUTO_INCREMENT DEFAULT NULL,
  `name` VARCHAR(20) NOT NULL DEFAULT 'NULL',
  `emission_per_km` FLOAT NOT NULL DEFAULT 0,
  PRIMARY KEY (`id`)
);

-- ---
-- Table 'AvailableInCountry'
-- 
-- ---

DROP TABLE IF EXISTS `availableincountry`;
		
CREATE TABLE `availableincountry` (
  `id` INT UNSIGNED NULL AUTO_INCREMENT DEFAULT NULL,
  `ingredient` INT UNSIGNED NOT NULL,
  `country` INT UNSIGNED NOT NULL,
  `transport_method` INT UNSIGNED NOT NULL,
  `production_type` VARCHAR(20) NULL DEFAULT NULL,
  `date_from` DATE NOT NULL,
  `date_until` DATE NOT NULL,
  PRIMARY KEY (`id`)
);

ALTER TABLE `availableincountry` ADD FOREIGN KEY (ingredient) REFERENCES `vegetalingredient` (`ingredient`)
    ON UPDATE CASCADE ON DELETE CASCADE;
ALTER TABLE `availableincountry` ADD FOREIGN KEY (country) REFERENCES `country` (`id`)
    ON UPDATE CASCADE ON DELETE CASCADE;
ALTER TABLE `availableincountry` ADD FOREIGN KEY (transport_method) REFERENCES `transportmethod` (`id`)
    ON UPDATE CASCADE ON DELETE CASCADE;


-- ---
-- Table 'Sea'
-- 
-- ---

DROP TABLE IF EXISTS `sea`;
		
CREATE TABLE `sea` (
  `id` INT UNSIGNED NULL AUTO_INCREMENT DEFAULT NULL,
  `name` VARCHAR(50) NOT NULL,
  `distance` INT UNSIGNED NOT NULL DEFAULT 0,
  PRIMARY KEY (`id`)
);

-- ---
-- Table 'AvailableInSea'
-- 
-- ---

DROP TABLE IF EXISTS `availableinsea`;
		
CREATE TABLE `availableinsea` (
  `id` INT UNSIGNED NULL AUTO_INCREMENT DEFAULT NULL,
  `ingredient` INT UNSIGNED NOT NULL,
  `sea` INT UNSIGNED NOT NULL,
  `transport_method` INT UNSIGNED NOT NULL,
  `date_from` DATE NOT NULL,
  `date_until` DATE NOT NULL,
  PRIMARY KEY (`id`)
);

ALTER TABLE `availableinsea` ADD FOREIGN KEY (ingredient) REFERENCES `ingredient` (`id`)
    ON UPDATE CASCADE ON DELETE CASCADE;
ALTER TABLE `availableinsea` ADD FOREIGN KEY (sea) REFERENCES `sea` (`id`)
    ON UPDATE CASCADE ON DELETE CASCADE;
ALTER TABLE `availableinsea` ADD FOREIGN KEY (transport_method) REFERENCES `transportmethod` (`id`)
    ON UPDATE CASCADE ON DELETE CASCADE;

-- ---
-- Table Properties
-- ---

-- ALTER TABLE `ingredient` ENGINE=InnoDB DEFAULT CHARSET=utf8 COLLATE=utf8_bin;
-- ALTER TABLE `synonym` ENGINE=InnoDB DEFAULT CHARSET=utf8 COLLATE=utf8_bin;
-- ALTER TABLE `unit` ENGINE=InnoDB DEFAULT CHARSET=utf8 COLLATE=utf8_bin;
-- ALTER TABLE `canuseunit` ENGINE=InnoDB DEFAULT CHARSET=utf8 COLLATE=utf8_bin;
-- ALTER TABLE `vegetalingredient` ENGINE=InnoDB DEFAULT CHARSET=utf8 COLLATE=utf8_bin;
-- ALTER TABLE `country` ENGINE=InnoDB DEFAULT CHARSET=utf8 COLLATE=utf8_bin;
-- ALTER TABLE `transportmethod` ENGINE=InnoDB DEFAULT CHARSET=utf8 COLLATE=utf8_bin;
-- ALTER TABLE `availableincountry` ENGINE=InnoDB DEFAULT CHARSET=utf8 COLLATE=utf8_bin;
-- ALTER TABLE `availableinsea` ENGINE=InnoDB DEFAULT CHARSET=utf8 COLLATE=utf8_bin;
-- ALTER TABLE `sea` ENGINE=InnoDB DEFAULT CHARSET=utf8 COLLATE=utf8_bin;


SET FOREIGN_KEY_CHECKS=1;
SET SQL_NOTES=@OLD_SQL_NOTES;