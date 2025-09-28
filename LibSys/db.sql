BEGIN TRANSACTION;
DROP TABLE IF EXISTS "Home_books";
CREATE TABLE "Home_books" ("book_name" varchar(200) NOT NULL, "quantity" integer unsigned NOT NULL CHECK ("quantity" >= 0), "author" text NOT NULL, "genre" text NULL, "fine" smallint unsigned NOT NULL CHECK ("fine" >= 0), "available_quantity" integer unsigned NOT NULL CHECK ("available_quantity" >= 0), "Bid" integer NOT NULL PRIMARY KEY);
DROP TABLE IF EXISTS "Home_issued";
CREATE TABLE "Home_issued" ("submit" bool NOT NULL, "create" datetime NOT NULL, "book_id" integer NOT NULL REFERENCES "Home_books" ("Bid") DEFERRABLE INITIALLY DEFERRED, "user_id" integer NULL REFERENCES "auth_user" ("id") DEFERRABLE INITIALLY DEFERRED, "Issue_No" integer NOT NULL PRIMARY KEY, "days" integer unsigned NOT NULL CHECK ("days" >= 0));
DROP TABLE IF EXISTS "auth_group";
CREATE TABLE "auth_group" ("id" integer NOT NULL PRIMARY KEY AUTOINCREMENT, "name" varchar(150) NOT NULL UNIQUE);
DROP TABLE IF EXISTS "auth_group_permissions";
CREATE TABLE "auth_group_permissions" ("id" integer NOT NULL PRIMARY KEY AUTOINCREMENT, "group_id" integer NOT NULL REFERENCES "auth_group" ("id") DEFERRABLE INITIALLY DEFERRED, "permission_id" integer NOT NULL REFERENCES "auth_permission" ("id") DEFERRABLE INITIALLY DEFERRED);
DROP TABLE IF EXISTS "auth_permission";
CREATE TABLE "auth_permission" ("id" integer NOT NULL PRIMARY KEY AUTOINCREMENT, "content_type_id" integer NOT NULL REFERENCES "django_content_type" ("id") DEFERRABLE INITIALLY DEFERRED, "codename" varchar(100) NOT NULL, "name" varchar(255) NOT NULL);
DROP TABLE IF EXISTS "auth_user";
CREATE TABLE "auth_user" ("id" integer NOT NULL PRIMARY KEY AUTOINCREMENT, "password" varchar(128) NOT NULL, "last_login" datetime NULL, "is_superuser" bool NOT NULL, "username" varchar(150) NOT NULL UNIQUE, "last_name" varchar(150) NOT NULL, "email" varchar(254) NOT NULL, "is_staff" bool NOT NULL, "is_active" bool NOT NULL, "date_joined" datetime NOT NULL, "first_name" varchar(150) NOT NULL);
DROP TABLE IF EXISTS "auth_user_groups";
CREATE TABLE "auth_user_groups" ("id" integer NOT NULL PRIMARY KEY AUTOINCREMENT, "user_id" integer NOT NULL REFERENCES "auth_user" ("id") DEFERRABLE INITIALLY DEFERRED, "group_id" integer NOT NULL REFERENCES "auth_group" ("id") DEFERRABLE INITIALLY DEFERRED);
DROP TABLE IF EXISTS "auth_user_user_permissions";
CREATE TABLE "auth_user_user_permissions" ("id" integer NOT NULL PRIMARY KEY AUTOINCREMENT, "user_id" integer NOT NULL REFERENCES "auth_user" ("id") DEFERRABLE INITIALLY DEFERRED, "permission_id" integer NOT NULL REFERENCES "auth_permission" ("id") DEFERRABLE INITIALLY DEFERRED);
DROP TABLE IF EXISTS "authtoken_token";
CREATE TABLE "authtoken_token" ("key" varchar(40) NOT NULL PRIMARY KEY, "created" datetime NOT NULL, "user_id" integer NOT NULL UNIQUE REFERENCES "auth_user" ("id") DEFERRABLE INITIALLY DEFERRED);
DROP TABLE IF EXISTS "django_admin_log";
CREATE TABLE "django_admin_log" ("id" integer NOT NULL PRIMARY KEY AUTOINCREMENT, "object_id" text NULL, "object_repr" varchar(200) NOT NULL, "action_flag" smallint unsigned NOT NULL CHECK ("action_flag" >= 0), "change_message" text NOT NULL, "content_type_id" integer NULL REFERENCES "django_content_type" ("id") DEFERRABLE INITIALLY DEFERRED, "user_id" integer NOT NULL REFERENCES "auth_user" ("id") DEFERRABLE INITIALLY DEFERRED, "action_time" datetime NOT NULL);
DROP TABLE IF EXISTS "django_content_type";
CREATE TABLE "django_content_type" ("id" integer NOT NULL PRIMARY KEY AUTOINCREMENT, "app_label" varchar(100) NOT NULL, "model" varchar(100) NOT NULL);
DROP TABLE IF EXISTS "django_migrations";
CREATE TABLE "django_migrations" ("id" integer NOT NULL PRIMARY KEY AUTOINCREMENT, "app" varchar(255) NOT NULL, "name" varchar(255) NOT NULL, "applied" datetime NOT NULL);
DROP TABLE IF EXISTS "django_session";
CREATE TABLE "django_session" ("session_key" varchar(40) NOT NULL PRIMARY KEY, "session_data" text NOT NULL, "expire_date" datetime NOT NULL);
INSERT INTO "Home_books" ("book_name","quantity","author","genre","fine","available_quantity","Bid") VALUES ('book1',12,'meme','comedy',123,12,1),
 ('book5',45,'akhil','comedy',456,45,2),
 ('apibook',1,'api','api',50,1,3);
INSERT INTO "Home_issued" ("submit","create","book_id","user_id","Issue_No","days") VALUES (1,'2024-12-19 08:18:32.582570',1,1,1,10),
 (1,'2024-12-19 08:18:35.146062',2,1,2,10),
 (1,'2024-12-21 10:27:20.347854',2,1,3,10),
 (0,'2025-09-25 09:54:48.257158',1,1,4,10),
 (0,'2025-09-25 09:54:51.005393',1,1,5,10);
INSERT INTO "auth_permission" ("id","content_type_id","codename","name") VALUES (1,1,'add_logentry','Can add log entry'),
 (2,1,'change_logentry','Can change log entry'),
 (3,1,'delete_logentry','Can delete log entry'),
 (4,1,'view_logentry','Can view log entry'),
 (5,2,'add_permission','Can add permission'),
 (6,2,'change_permission','Can change permission'),
 (7,2,'delete_permission','Can delete permission'),
 (8,2,'view_permission','Can view permission'),
 (9,3,'add_group','Can add group'),
 (10,3,'change_group','Can change group'),
 (11,3,'delete_group','Can delete group'),
 (12,3,'view_group','Can view group'),
 (13,4,'add_user','Can add user'),
 (14,4,'change_user','Can change user'),
 (15,4,'delete_user','Can delete user'),
 (16,4,'view_user','Can view user'),
 (17,5,'add_contenttype','Can add content type'),
 (18,5,'change_contenttype','Can change content type'),
 (19,5,'delete_contenttype','Can delete content type'),
 (20,5,'view_contenttype','Can view content type'),
 (21,6,'add_session','Can add session'),
 (22,6,'change_session','Can change session'),
 (23,6,'delete_session','Can delete session'),
 (24,6,'view_session','Can view session'),
 (25,7,'add_issued','Can add issued'),
 (26,7,'change_issued','Can change issued'),
 (27,7,'delete_issued','Can delete issued'),
 (28,7,'view_issued','Can view issued'),
 (29,8,'add_books','Can add books'),
 (30,8,'change_books','Can change books'),
 (31,8,'delete_books','Can delete books'),
 (32,8,'view_books','Can view books'),
 (33,9,'add_token','Can add Token'),
 (34,9,'change_token','Can change Token'),
 (35,9,'delete_token','Can delete Token'),
 (36,9,'view_token','Can view Token'),
 (37,10,'add_tokenproxy','Can add Token'),
 (38,10,'change_tokenproxy','Can change Token'),
 (39,10,'delete_tokenproxy','Can delete Token'),
 (40,10,'view_tokenproxy','Can view Token');
INSERT INTO "auth_user" ("id","password","last_login","is_superuser","username","last_name","email","is_staff","is_active","date_joined","first_name") VALUES (1,'pbkdf2_sha256$600000$TfyWQtXaVwwgvrjFvcu6KP$q5jfNZfI5d9c11FludgfiF6N0PrkTLYUHZzbuy1If4M=','2025-09-25 09:47:44.970760',1,'akhil161','','akhilkarwal161@gmail.com',1,1,'2024-12-15 09:54:46.932136',''),
 (2,'pbkdf2_sha256$600000$8xJHgzxwPzaG6Gi8l9rNwI$eotnDsslEbzKLyBv0f1dCiJ5PNxfWRsvuLQiBrCc43w=','2024-12-18 12:53:41.060362',0,'archita','','',0,1,'2024-12-18 12:12:51.213530','');
INSERT INTO "django_content_type" ("id","app_label","model") VALUES (1,'admin','logentry'),
 (2,'auth','permission'),
 (3,'auth','group'),
 (4,'auth','user'),
 (5,'contenttypes','contenttype'),
 (6,'sessions','session'),
 (7,'Home','issued'),
 (8,'Home','books'),
 (9,'authtoken','token'),
 (10,'authtoken','tokenproxy');
INSERT INTO "django_migrations" ("id","app","name","applied") VALUES (1,'contenttypes','0001_initial','2024-12-15 09:54:10.456096'),
 (2,'auth','0001_initial','2024-12-15 09:54:10.477672'),
 (3,'admin','0001_initial','2024-12-15 09:54:10.494188'),
 (4,'admin','0002_logentry_remove_auto_add','2024-12-15 09:54:10.506963'),
 (5,'admin','0003_logentry_add_action_flag_choices','2024-12-15 09:54:10.517480'),
 (6,'contenttypes','0002_remove_content_type_name','2024-12-15 09:54:10.539125'),
 (7,'auth','0002_alter_permission_name_max_length','2024-12-15 09:54:10.553046'),
 (8,'auth','0003_alter_user_email_max_length','2024-12-15 09:54:10.570147'),
 (9,'auth','0004_alter_user_username_opts','2024-12-15 09:54:10.580105'),
 (10,'auth','0005_alter_user_last_login_null','2024-12-15 09:54:10.594210'),
 (11,'auth','0006_require_contenttypes_0002','2024-12-15 09:54:10.599636'),
 (12,'auth','0007_alter_validators_add_error_messages','2024-12-15 09:54:10.609611'),
 (13,'auth','0008_alter_user_username_max_length','2024-12-15 09:54:10.624756'),
 (14,'auth','0009_alter_user_last_name_max_length','2024-12-15 09:54:10.637000'),
 (15,'auth','0010_alter_group_name_max_length','2024-12-15 09:54:10.653456'),
 (16,'auth','0011_update_proxy_permissions','2024-12-15 09:54:10.662898'),
 (17,'auth','0012_alter_user_first_name_max_length','2024-12-15 09:54:10.678128'),
 (18,'sessions','0001_initial','2024-12-15 09:54:10.687042'),
 (19,'Home','0001_initial','2024-12-15 12:47:44.834735'),
 (20,'Home','0002_books_id_alter_books_bid_alter_issued_issued_bid','2024-12-15 13:05:43.167025'),
 (21,'Home','0003_books_available_quantity','2024-12-15 13:16:39.638935'),
 (22,'Home','0004_alter_books_available_quantity','2024-12-16 13:22:54.435062'),
 (23,'Home','0005_remove_issued_issued_bid_issued_issue_no_and_more','2024-12-17 11:26:17.032167'),
 (24,'Home','0006_alter_issued_issue_no','2024-12-17 11:26:17.057395'),
 (25,'Home','0007_alter_issued_issue_no','2024-12-17 17:23:44.923154'),
 (26,'Home','0008_alter_books_bid_alter_issued_issue_no','2024-12-18 08:14:52.070955'),
 (27,'Home','0009_remove_books_id_alter_books_bid','2024-12-18 08:28:31.384082'),
 (28,'Home','0010_alter_issued_days','2024-12-18 12:26:01.729710'),
 (29,'authtoken','0001_initial','2024-12-22 05:32:39.404993'),
 (30,'authtoken','0002_auto_20160226_1747','2024-12-22 05:32:39.430101'),
 (31,'authtoken','0003_tokenproxy','2024-12-22 05:32:39.439525'),
 (32,'authtoken','0004_alter_tokenproxy_options','2024-12-22 05:32:39.446672');
INSERT INTO "django_session" ("session_key","session_data","expire_date") VALUES ('iue0e6tzceo7buvbvq92f8w2o0riaibo','e30:1tMnH3:MtB68aZVEekhz9S0tSkiJaaYTqFU0gtPUzoj1ykiNqQ','2024-12-29 11:59:01.593295'),
 ('hkx8uxdl75oi1tpbpax000qdtv1rebvg','e30:1tMnMh:6es6i6w0srwim1rqrtdRctRnLRUJG0zOzo4v16jKGzU','2024-12-29 12:04:51.109698'),
 ('as5qwdm99siv4tporwuj4vrq4gqkf8lx','e30:1tMnQ9:fMBWGKqKoKtbEDGl0VVsSMwpxSIvxIQGYQWZVgpmEss','2024-12-29 12:08:25.678111'),
 ('adin1kg9pl2q1owf8puk6vcxa82en8ld','e30:1tMnQw:orJbkQSw8bAU40-6bK-oNFKl2hMjzHsvirwNKKN7Ot8','2024-12-29 12:09:14.584973'),
 ('l35wlekrofyad7ilz6n3u1btvs1fhmlk','e30:1tNsv5:QSsJSxJYW2DFBpcUOu4p0DwP5U5hJ-JHx2EmgdkGhOM','2025-01-01 12:12:51.416526'),
 ('znt8a7jga4ihckr8fip0z21zwttcmsa4','.eJxVjEEOwiAQRe_C2hBhYAou3fcMZICpVA0kpV0Z765NutDtf-_9lwi0rSVsnZcwZ3ERWpx-t0jpwXUH-U711mRqdV3mKHdFHrTLsWV-Xg_376BQL9_aI1kPfsCYyaBicDrbM1jlcGDtSSGxsipiNkyAUyJnLSUCNuwnAPH-AMesN6s:1tNsw4:Gi9vm-4Am9aSYG-Ciy4LRFM8zo2olBpZK-5cWvTZVSo','2025-01-01 12:13:52.189621'),
 ('90qaalmhb57jtd5b1zya557ifzouigt4','.eJxVjEEOwiAQRe_C2hBhYAou3fcMZICpVA0kpV0Z765NutDtf-_9lwi0rSVsnZcwZ3ERWpx-t0jpwXUH-U711mRqdV3mKHdFHrTLsWV-Xg_376BQL9_aI1kPfsCYyaBicDrbM1jlcGDtSSGxsipiNkyAUyJnLSUCNuwnAPH-AMesN6s:1tNtYb:eGcndWQ9MHcny2caOhUmXyF4ZXQvUtq7oeRB_BOepmA','2025-01-01 12:53:41.075983'),
 ('pzu0e664gvyxi0q8ceid3d73855v41es','.eJxVjcEOwiAQRP-FsyGAhbIevfcbCLuLUjWQlPZk_Hdp0oOeJpl5M_MWIW5rDltLS5hZXIQWp18PIz1T2QN-xHKvkmpZlxnljsgjbXKqnF7Xg_0byLHl3iYyIxtPCcifI7MF52xC0ArsrQt4CwCenUFjBlTg3WAZbX9QekQlPl_kszeO:1tOwgl:djOI3MeQPExVjSBiWfENNOXshsuS4dUVx_hQqXZAWJI','2025-01-04 10:26:27.014473'),
 ('0oqif9tmzpj6mevqirull97kk01uxntq','.eJxVjMsOwiAUBf-FtSEgtIhL9_0GcrkPqRqalHZl_HfbpAvdnpk5b5VgXUpaG89pJHVVVp1-twz45LoDekC9Txqnusxj1ruiD9r0MBG_bof7d1Cgla2OyD1nMYGsCyxkkCSC68k7FvSxixfC7Gw-Q4iUxQuidd4hmm7LrPp8AR-sOU8:1v1iZk:nkYYvMSuFuAW8-1rCQBOGD6RVy3gFpUfeaWhqr9Vp3M','2025-10-09 09:47:44.980160');
DROP INDEX IF EXISTS "Home_issued_book_id_50a169be";
CREATE INDEX "Home_issued_book_id_50a169be" ON "Home_issued" ("book_id");
DROP INDEX IF EXISTS "Home_issued_user_id_d88d11f0";
CREATE INDEX "Home_issued_user_id_d88d11f0" ON "Home_issued" ("user_id");
DROP INDEX IF EXISTS "auth_group_permissions_group_id_b120cbf9";
CREATE INDEX "auth_group_permissions_group_id_b120cbf9" ON "auth_group_permissions" ("group_id");
DROP INDEX IF EXISTS "auth_group_permissions_group_id_permission_id_0cd325b0_uniq";
CREATE UNIQUE INDEX "auth_group_permissions_group_id_permission_id_0cd325b0_uniq" ON "auth_group_permissions" ("group_id", "permission_id");
DROP INDEX IF EXISTS "auth_group_permissions_permission_id_84c5c92e";
CREATE INDEX "auth_group_permissions_permission_id_84c5c92e" ON "auth_group_permissions" ("permission_id");
DROP INDEX IF EXISTS "auth_permission_content_type_id_2f476e4b";
CREATE INDEX "auth_permission_content_type_id_2f476e4b" ON "auth_permission" ("content_type_id");
DROP INDEX IF EXISTS "auth_permission_content_type_id_codename_01ab375a_uniq";
CREATE UNIQUE INDEX "auth_permission_content_type_id_codename_01ab375a_uniq" ON "auth_permission" ("content_type_id", "codename");
DROP INDEX IF EXISTS "auth_user_groups_group_id_97559544";
CREATE INDEX "auth_user_groups_group_id_97559544" ON "auth_user_groups" ("group_id");
DROP INDEX IF EXISTS "auth_user_groups_user_id_6a12ed8b";
CREATE INDEX "auth_user_groups_user_id_6a12ed8b" ON "auth_user_groups" ("user_id");
DROP INDEX IF EXISTS "auth_user_groups_user_id_group_id_94350c0c_uniq";
CREATE UNIQUE INDEX "auth_user_groups_user_id_group_id_94350c0c_uniq" ON "auth_user_groups" ("user_id", "group_id");
DROP INDEX IF EXISTS "auth_user_user_permissions_permission_id_1fbb5f2c";
CREATE INDEX "auth_user_user_permissions_permission_id_1fbb5f2c" ON "auth_user_user_permissions" ("permission_id");
DROP INDEX IF EXISTS "auth_user_user_permissions_user_id_a95ead1b";
CREATE INDEX "auth_user_user_permissions_user_id_a95ead1b" ON "auth_user_user_permissions" ("user_id");
DROP INDEX IF EXISTS "auth_user_user_permissions_user_id_permission_id_14a6b632_uniq";
CREATE UNIQUE INDEX "auth_user_user_permissions_user_id_permission_id_14a6b632_uniq" ON "auth_user_user_permissions" ("user_id", "permission_id");
DROP INDEX IF EXISTS "django_admin_log_content_type_id_c4bce8eb";
CREATE INDEX "django_admin_log_content_type_id_c4bce8eb" ON "django_admin_log" ("content_type_id");
DROP INDEX IF EXISTS "django_admin_log_user_id_c564eba6";
CREATE INDEX "django_admin_log_user_id_c564eba6" ON "django_admin_log" ("user_id");
DROP INDEX IF EXISTS "django_content_type_app_label_model_76bd3d3b_uniq";
CREATE UNIQUE INDEX "django_content_type_app_label_model_76bd3d3b_uniq" ON "django_content_type" ("app_label", "model");
DROP INDEX IF EXISTS "django_session_expire_date_a5c62663";
CREATE INDEX "django_session_expire_date_a5c62663" ON "django_session" ("expire_date");
COMMIT;
