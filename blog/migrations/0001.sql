BEGIN;
--
-- Create model Content
--
CREATE TABLE `blog_content` (
    `id` integer AUTO_INCREMENT NOT NULL PRIMARY KEY,
    `title` varchar(200) NOT NULL,
    `slug` varchar(200) NOT NULL UNIQUE,
    `create_time` datetime(6) NOT NULL,
    `edit_time` datetime(6) NOT NULL,
    `summary` longtext NOT NULL,
    `text` longtext NOT NULL,
    `priority_id` integer NOT NULL,
    `type` varchar(16) NOT NULL
);
--
-- Create model Link
--
CREATE TABLE `blog_link` (
    `id` integer AUTO_INCREMENT NOT NULL PRIMARY KEY,
    `name` varchar(200) NOT NULL,
    `url` varchar(200) NOT NULL
);
--
-- Create model Meta
--
CREATE TABLE `blog_meta` (
    `id` integer AUTO_INCREMENT NOT NULL PRIMARY KEY,
    `name` varchar(200) NOT NULL,
    `slug` varchar(200) NOT NULL UNIQUE,
    `type` varchar(32) NOT NULL,
    `description` longtext NOT NULL,
    `priority_id` integer NOT NULL
);
--
-- Create model Setting
--
CREATE TABLE `blog_setting` (
    `id` integer AUTO_INCREMENT NOT NULL PRIMARY KEY,
    `name` varchar(32) NOT NULL,
    `value` longtext NOT NULL
);
--
-- Create model User
--
CREATE TABLE `blog_user` (
    `id` integer AUTO_INCREMENT NOT NULL PRIMARY KEY,
    `username` varchar(32) NOT NULL UNIQUE,
    `password` varchar(64) NOT NULL,
    `mail` varchar(200) NOT NULL UNIQUE,
    `url` varchar(200) NOT NULL,
    `nickname` varchar(32) NOT NULL UNIQUE,
    `create_time` datetime(6) NOT NULL,
    `last_login_time` datetime(6) NOT NULL,
    `group` varchar(32) NOT NULL
);
--
-- Create model Relationship
--
CREATE TABLE `blog_relationship` (
    `id` integer AUTO_INCREMENT NOT NULL PRIMARY KEY,
    `content_id_id` integer NOT NULL,
    `meta_id_id` integer NOT NULL
);
--
-- Add field author_id to content
--
ALTER TABLE `blog_content` ADD COLUMN `author_id_id` integer NOT NULL;
--
-- Create model Comment
--
CREATE TABLE `blog_comment` (
    `id` integer AUTO_INCREMENT NOT NULL PRIMARY KEY,
    `create_time` datetime(6) NOT NULL,
    `edit_time` datetime(6) NOT NULL,
    `author_ip` varchar(64) NOT NULL,
    `status` varchar(16) NOT NULL,
    `text` longtext NOT NULL,
    `author_id_id` integer NOT NULL,
    `content_id_id` integer NOT NULL,
    `parent_id` integer NOT NULL
);

ALTER TABLE `blog_relationship` ADD CONSTRAINT `blog_relationship_content_id_id_3c2b5fda_fk_blog_content_id` FOREIGN KEY (`content_id_id`) REFERENCES `blog_content` (`id`);
ALTER TABLE `blog_relationship` ADD CONSTRAINT `blog_relationship_meta_id_id_321cc8c4_fk_blog_meta_id` FOREIGN KEY (`meta_id_id`) REFERENCES `blog_meta` (`id`);
ALTER TABLE `blog_content` ADD CONSTRAINT `blog_content_author_id_id_b738f7c8_fk_blog_user_id` FOREIGN KEY (`author_id_id`) REFERENCES `blog_user` (`id`);
ALTER TABLE `blog_comment` ADD CONSTRAINT `blog_comment_author_id_id_62148427_fk_blog_user_id` FOREIGN KEY (`author_id_id`) REFERENCES `blog_user` (`id`);
ALTER TABLE `blog_comment` ADD CONSTRAINT `blog_comment_content_id_id_10dd47d1_fk_blog_content_id` FOREIGN KEY (`content_id_id`) REFERENCES `blog_content` (`id`);
ALTER TABLE `blog_comment` ADD CONSTRAINT `blog_comment_parent_id_f2a027bb_fk_blog_comment_id` FOREIGN KEY (`parent_id`) REFERENCES `blog_comment` (`id`);

COMMIT;