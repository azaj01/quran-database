-- Same data as the real dump would carry, but with `surahs` listing name_en
-- before name_ar, and `editions` listing format before englishName. A
-- positional INSERT loads both tables into the wrong columns without error.
INSERT INTO `surahs` (`id`, `number`, `name_en`, `name_ar`, `name_en_translation`, `type`, `created_at`, `updated_at`) VALUES
(1, 1, 'Al-Fatiha', 'الفاتحة', 'The Opening', 'Meccan', NULL, NULL);

INSERT INTO `ayahs` (`id`, `number`, `text`, `number_in_surah`, `page`, `surah_id`, `hizb_id`, `juz_id`, `sajda`, `created_at`, `updated_at`) VALUES
(1, 1, 'بِسْمِ ٱللَّهِ', 1, 1, 1, 1, 1, 0, NULL, NULL);

INSERT INTO `editions` (`id`, `identifier`, `language`, `name`, `format`, `englishName`, `type`, `created_at`, `updated_at`) VALUES
(1, 'en.sahih', 'en', 'Saheeh International', 'text', 'Saheeh International', 'translation', NULL, NULL);

INSERT INTO `ayah_edition` (`id`, `ayah_id`, `edition_id`, `data`, `is_audio`, `created_at`, `updated_at`) VALUES
(1, 1, 1, 'In the name of Allah', 0, NULL, NULL);
