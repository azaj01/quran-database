INSERT INTO `ayahs` (`id`, `number`, `text`, `number_in_surah`, `page`, `surah_id`, `hizb_id`, `juz_id`, `sajda`, `created_at`, `updated_at`) VALUES
(1, 1, 'بِسْمِ ٱللَّهِ', 1, 1, 1, 1, 1, 0, NULL, NULL);
INSERT INTO `ayah_edition` (`id`, `ayah_id`, `edition_id`, `data`, `is_audio`, `created_at`, `updated_at`) VALUES
(1, 1, 1, 'In the name of Allah', 0, NULL, NULL);
INSERT INTO `editions` (`id`, `identifier`, `language`, `name`, `english_name`, `format`, `type`, `created_at`, `updated_at`) VALUES
(1, 'en.test', 'en', 'Test', 'Test', 'text', 'translation', NULL, NULL);
INSERT INTO `surahs` (`id`, `number`, `name_ar`, `name_en`, `name_en_translation`, `type`, `created_at`, `updated_at`) VALUES
(1, 1, 'الفاتحة', 'Al-Faatiha', 'The Opening', 'Meccan', NULL, NULL);
