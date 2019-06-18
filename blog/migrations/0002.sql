BEGIN;
--
-- Alter field parent on comment
--
ALTER TABLE `blog_comment` CHANGE `parent_id` `parent` integer NOT NULL;
COMMIT;
