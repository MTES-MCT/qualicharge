PGDMP  	    8    1            	    |            qualicharge-api "   14.11 (Ubuntu 14.11-1.pgdg22.04+1) "   14.11 (Ubuntu 14.11-1.pgdg22.04+1) O    �           0    0    ENCODING    ENCODING        SET client_encoding = 'UTF8';
                      false            �           0    0 
   STDSTRINGS 
   STDSTRINGS     (   SET standard_conforming_strings = 'on';
                      false            �           0    0 
   SEARCHPATH 
   SEARCHPATH     8   SELECT pg_catalog.set_config('search_path', '', false);
                      false            �           1262    16384    qualicharge-api    DATABASE     b   CREATE DATABASE "qualicharge-api" WITH TEMPLATE = template0 ENCODING = 'UTF8' LOCALE = 'C.UTF-8';
 !   DROP DATABASE "qualicharge-api";
                qualicharge    false                        3079    17796    timescaledb 	   EXTENSION     ?   CREATE EXTENSION IF NOT EXISTS timescaledb WITH SCHEMA public;
    DROP EXTENSION timescaledb;
                   false            �           0    0    EXTENSION timescaledb    COMMENT     |   COMMENT ON EXTENSION timescaledb IS 'Enables scalable inserts and complex queries for time-series data (Apache 2 Edition)';
                        false    3                        3079    18653    postgis 	   EXTENSION     ;   CREATE EXTENSION IF NOT EXISTS postgis WITH SCHEMA public;
    DROP EXTENSION postgis;
                   false            �           0    0    EXTENSION postgis    COMMENT     ^   COMMENT ON EXTENSION postgis IS 'PostGIS geometry and geography spatial types and functions';
                        false    2            U           1247    19829    accessibilitepmrenum    TYPE     �   CREATE TYPE public.accessibilitepmrenum AS ENUM (
    'RESERVE_PMR',
    'NON_RESERVE',
    'NON_ACCESSIBLE',
    'INCONNUE'
);
 '   DROP TYPE public.accessibilitepmrenum;
       public          qualicharge    false            L           1247    19788    conditionaccesenum    TYPE     \   CREATE TYPE public.conditionaccesenum AS ENUM (
    'ACCESS_LIBRE',
    'ACCESS_RESERVE'
);
 %   DROP TYPE public.conditionaccesenum;
       public          qualicharge    false            ^           1247    19879    etatpdcenum    TYPE     `   CREATE TYPE public.etatpdcenum AS ENUM (
    'EN_SERVICE',
    'HORS_SERVICE',
    'INCONNU'
);
    DROP TYPE public.etatpdcenum;
       public          qualicharge    false            d           1247    19896    etatpriseenum    TYPE     c   CREATE TYPE public.etatpriseenum AS ENUM (
    'FONCTIONNEL',
    'HORS_SERVICE',
    'INCONNU'
);
     DROP TYPE public.etatpriseenum;
       public          qualicharge    false            I           1247    19777    implantationstationenum    TYPE     �   CREATE TYPE public.implantationstationenum AS ENUM (
    'VOIRIE',
    'PARKING_PUBLIC',
    'PARKING_PRIVE_USAGE_PUBLIC',
    'PARKING_PRIVE_CLIENTELE',
    'STATION_RECHARGE_RAPIDE'
);
 *   DROP TYPE public.implantationstationenum;
       public          qualicharge    false            a           1247    19886    occupationpdcenum    TYPE     j   CREATE TYPE public.occupationpdcenum AS ENUM (
    'LIBRE',
    'OCCUPE',
    'RESERVE',
    'INCONNU'
);
 $   DROP TYPE public.occupationpdcenum;
       public          qualicharge    false            j           1247    19915    operationalunittypeenum    TYPE     W   CREATE TYPE public.operationalunittypeenum AS ENUM (
    'CHARGING',
    'MOBILITY'
);
 *   DROP TYPE public.operationalunittypeenum;
       public          qualicharge    false            O           1247    19794    raccordementemum    TYPE     N   CREATE TYPE public.raccordementemum AS ENUM (
    'DIRECT',
    'INDIRECT'
);
 #   DROP TYPE public.raccordementemum;
       public          qualicharge    false                       1259    19730    alembic_version    TABLE     X   CREATE TABLE public.alembic_version (
    version_num character varying(32) NOT NULL
);
 #   DROP TABLE public.alembic_version;
       public         heap    qualicharge    false                       1259    19735 	   amenageur    TABLE     Z  CREATE TABLE public.amenageur (
    created_at timestamp with time zone NOT NULL,
    updated_at timestamp with time zone NOT NULL,
    id uuid NOT NULL,
    nom_amenageur character varying,
    siren_amenageur character varying,
    contact_amenageur character varying,
    CONSTRAINT "pre-creation-update" CHECK ((created_at <= updated_at))
);
    DROP TABLE public.amenageur;
       public         heap    qualicharge    false                       1259    21926    city    TABLE     t  CREATE TABLE public.city (
    created_at timestamp with time zone NOT NULL,
    updated_at timestamp with time zone NOT NULL,
    id uuid NOT NULL,
    name character varying NOT NULL,
    geometry public.geometry(Geometry,4326) NOT NULL,
    code character varying NOT NULL,
    department_id uuid,
    epci_id uuid,
    population integer,
    area double precision
);
    DROP TABLE public.city;
       public         heap    qualicharge    false    2    2    2    2    2    2    2    2                       1259    23565 
   department    TABLE     d  CREATE TABLE public.department (
    created_at timestamp with time zone NOT NULL,
    updated_at timestamp with time zone NOT NULL,
    id uuid NOT NULL,
    name character varying NOT NULL,
    geometry public.geometry(Geometry,4326) NOT NULL,
    code character varying NOT NULL,
    region_id uuid,
    population integer,
    area double precision
);
    DROP TABLE public.department;
       public         heap    qualicharge    false    2    2    2    2    2    2    2    2                       1259    19745    enseigne    TABLE       CREATE TABLE public.enseigne (
    created_at timestamp with time zone NOT NULL,
    updated_at timestamp with time zone NOT NULL,
    id uuid NOT NULL,
    nom_enseigne character varying NOT NULL,
    CONSTRAINT "pre-creation-update" CHECK ((created_at <= updated_at))
);
    DROP TABLE public.enseigne;
       public         heap    qualicharge    false                        1259    23882    epci    TABLE     J  CREATE TABLE public.epci (
    created_at timestamp with time zone NOT NULL,
    updated_at timestamp with time zone NOT NULL,
    id uuid NOT NULL,
    name character varying NOT NULL,
    geometry public.geometry(Geometry,4326) NOT NULL,
    code character varying NOT NULL,
    population integer,
    area double precision
);
    DROP TABLE public.epci;
       public         heap    qualicharge    false    2    2    2    2    2    2    2    2                       1259    19933    group    TABLE       CREATE TABLE public."group" (
    created_at timestamp with time zone NOT NULL,
    updated_at timestamp with time zone NOT NULL,
    id uuid NOT NULL,
    name character varying NOT NULL,
    CONSTRAINT "pre-creation-update" CHECK ((created_at <= updated_at))
);
    DROP TABLE public."group";
       public         heap    qualicharge    false                       1259    19953    groupoperationalunit    TABLE     p   CREATE TABLE public.groupoperationalunit (
    group_id uuid NOT NULL,
    operational_unit_id uuid NOT NULL
);
 (   DROP TABLE public.groupoperationalunit;
       public         heap    qualicharge    false                       1259    19755    localisation    TABLE     �  CREATE TABLE public.localisation (
    created_at timestamp with time zone NOT NULL,
    updated_at timestamp with time zone NOT NULL,
    id uuid NOT NULL,
    adresse_station character varying NOT NULL,
    code_insee_commune character varying NOT NULL,
    "coordonneesXY" public.geometry(Point,4326) NOT NULL,
    CONSTRAINT "pre-creation-update" CHECK ((created_at <= updated_at))
);
     DROP TABLE public.localisation;
       public         heap    qualicharge    false    2    2    2    2    2    2    2    2                       1259    19766 	   operateur    TABLE     g  CREATE TABLE public.operateur (
    created_at timestamp with time zone NOT NULL,
    updated_at timestamp with time zone NOT NULL,
    id uuid NOT NULL,
    nom_operateur character varying,
    contact_operateur character varying NOT NULL,
    telephone_operateur character varying,
    CONSTRAINT "pre-creation-update" CHECK ((created_at <= updated_at))
);
    DROP TABLE public.operateur;
       public         heap    qualicharge    false                       1259    19919    operationalunit    TABLE     g  CREATE TABLE public.operationalunit (
    created_at timestamp with time zone NOT NULL,
    updated_at timestamp with time zone NOT NULL,
    id uuid NOT NULL,
    code character varying NOT NULL,
    name character varying NOT NULL,
    type public.operationalunittypeenum NOT NULL,
    CONSTRAINT "pre-creation-update" CHECK ((created_at <= updated_at))
);
 #   DROP TABLE public.operationalunit;
       public         heap    qualicharge    false    2154                       1259    19837    pointdecharge    TABLE     �  CREATE TABLE public.pointdecharge (
    created_at timestamp with time zone NOT NULL,
    updated_at timestamp with time zone NOT NULL,
    id uuid NOT NULL,
    id_pdc_itinerance character varying NOT NULL,
    id_pdc_local character varying,
    puissance_nominale double precision NOT NULL,
    prise_type_ef boolean NOT NULL,
    prise_type_2 boolean NOT NULL,
    prise_type_combo_ccs boolean NOT NULL,
    prise_type_chademo boolean NOT NULL,
    prise_type_autre boolean NOT NULL,
    gratuit boolean,
    paiement_acte boolean NOT NULL,
    paiement_cb boolean,
    paiement_autre boolean,
    tarification character varying,
    reservation boolean NOT NULL,
    accessibilite_pmr public.accessibilitepmrenum NOT NULL,
    restriction_gabarit character varying NOT NULL,
    observations character varying,
    cable_t2_attache boolean,
    station_id uuid,
    CONSTRAINT "pre-creation-update" CHECK ((created_at <= updated_at))
);
 !   DROP TABLE public.pointdecharge;
       public         heap    qualicharge    false    2133            !           1259    25719    region    TABLE     L  CREATE TABLE public.region (
    created_at timestamp with time zone NOT NULL,
    updated_at timestamp with time zone NOT NULL,
    id uuid NOT NULL,
    name character varying NOT NULL,
    geometry public.geometry(Geometry,4326) NOT NULL,
    code character varying NOT NULL,
    population integer,
    area double precision
);
    DROP TABLE public.region;
       public         heap    qualicharge    false    2    2    2    2    2    2    2    2                       1259    19867    session    TABLE     �  CREATE TABLE public.session (
    energy double precision NOT NULL,
    created_at timestamp with time zone NOT NULL,
    updated_at timestamp with time zone NOT NULL,
    id uuid NOT NULL,
    start timestamp with time zone NOT NULL,
    "end" timestamp with time zone NOT NULL,
    point_de_charge_id uuid,
    CONSTRAINT "pre-creation-update" CHECK ((created_at <= updated_at))
);
    DROP TABLE public.session;
       public         heap    qualicharge    false                       1259    19799    station    TABLE     X  CREATE TABLE public.station (
    created_at timestamp with time zone NOT NULL,
    updated_at timestamp with time zone NOT NULL,
    id uuid NOT NULL,
    id_station_itinerance character varying NOT NULL,
    id_station_local character varying,
    nom_station character varying NOT NULL,
    implantation_station public.implantationstationenum NOT NULL,
    nbre_pdc integer NOT NULL,
    condition_acces public.conditionaccesenum NOT NULL,
    horaires character varying NOT NULL,
    station_deux_roues boolean NOT NULL,
    raccordement public.raccordementemum,
    num_pdl character varying,
    date_maj date NOT NULL,
    date_mise_en_service date,
    amenageur_id uuid,
    operateur_id uuid,
    enseigne_id uuid,
    localisation_id uuid,
    operational_unit_id uuid,
    CONSTRAINT "pre-creation-update" CHECK ((created_at <= updated_at))
);
    DROP TABLE public.station;
       public         heap    qualicharge    false    2121    2124    2127                       1259    19903    status    TABLE     P  CREATE TABLE public.status (
    etat_pdc public.etatpdcenum NOT NULL,
    occupation_pdc public.occupationpdcenum NOT NULL,
    etat_prise_type_2 public.etatpriseenum,
    etat_prise_type_combo_ccs public.etatpriseenum,
    etat_prise_type_chademo public.etatpriseenum,
    etat_prise_type_ef public.etatpriseenum,
    created_at timestamp with time zone NOT NULL,
    updated_at timestamp with time zone NOT NULL,
    id uuid NOT NULL,
    horodatage timestamp with time zone NOT NULL,
    point_de_charge_id uuid,
    CONSTRAINT "pre-creation-update" CHECK ((created_at <= updated_at))
);
    DROP TABLE public.status;
       public         heap    qualicharge    false    2148    2148    2148    2142    2145    2148                       1259    19943    user    TABLE     Q  CREATE TABLE public."user" (
    created_at timestamp with time zone NOT NULL,
    updated_at timestamp with time zone NOT NULL,
    id uuid NOT NULL,
    username character varying NOT NULL,
    email character varying NOT NULL,
    first_name character varying,
    last_name character varying,
    is_active boolean NOT NULL,
    is_staff boolean NOT NULL,
    is_superuser boolean NOT NULL,
    scopes character varying[] NOT NULL,
    password character varying NOT NULL,
    last_login timestamp with time zone,
    CONSTRAINT "pre-creation-update" CHECK ((created_at <= updated_at))
);
    DROP TABLE public."user";
       public         heap    qualicharge    false                       1259    19968 	   usergroup    TABLE     Y   CREATE TABLE public.usergroup (
    user_id uuid NOT NULL,
    group_id uuid NOT NULL
);
    DROP TABLE public.usergroup;
       public         heap    qualicharge    false            �           2606    19734 #   alembic_version alembic_version_pkc 
   CONSTRAINT     j   ALTER TABLE ONLY public.alembic_version
    ADD CONSTRAINT alembic_version_pkc PRIMARY KEY (version_num);
 M   ALTER TABLE ONLY public.alembic_version DROP CONSTRAINT alembic_version_pkc;
       public            qualicharge    false    272            �           2606    19744 G   amenageur amenageur_nom_amenageur_siren_amenageur_contact_amenageur_key 
   CONSTRAINT     �   ALTER TABLE ONLY public.amenageur
    ADD CONSTRAINT amenageur_nom_amenageur_siren_amenageur_contact_amenageur_key UNIQUE (nom_amenageur, siren_amenageur, contact_amenageur);
 q   ALTER TABLE ONLY public.amenageur DROP CONSTRAINT amenageur_nom_amenageur_siren_amenageur_contact_amenageur_key;
       public            qualicharge    false    273    273    273            �           2606    19742    amenageur amenageur_pkey 
   CONSTRAINT     V   ALTER TABLE ONLY public.amenageur
    ADD CONSTRAINT amenageur_pkey PRIMARY KEY (id);
 B   ALTER TABLE ONLY public.amenageur DROP CONSTRAINT amenageur_pkey;
       public            qualicharge    false    273            �           2606    19754 "   enseigne enseigne_nom_enseigne_key 
   CONSTRAINT     e   ALTER TABLE ONLY public.enseigne
    ADD CONSTRAINT enseigne_nom_enseigne_key UNIQUE (nom_enseigne);
 L   ALTER TABLE ONLY public.enseigne DROP CONSTRAINT enseigne_nom_enseigne_key;
       public            qualicharge    false    274            �           2606    19752    enseigne enseigne_pkey 
   CONSTRAINT     T   ALTER TABLE ONLY public.enseigne
    ADD CONSTRAINT enseigne_pkey PRIMARY KEY (id);
 @   ALTER TABLE ONLY public.enseigne DROP CONSTRAINT enseigne_pkey;
       public            qualicharge    false    274            �           2606    19942    group group_name_key 
   CONSTRAINT     Q   ALTER TABLE ONLY public."group"
    ADD CONSTRAINT group_name_key UNIQUE (name);
 @   ALTER TABLE ONLY public."group" DROP CONSTRAINT group_name_key;
       public            qualicharge    false    282            �           2606    19940    group group_pkey 
   CONSTRAINT     P   ALTER TABLE ONLY public."group"
    ADD CONSTRAINT group_pkey PRIMARY KEY (id);
 <   ALTER TABLE ONLY public."group" DROP CONSTRAINT group_pkey;
       public            qualicharge    false    282            �           2606    19957 .   groupoperationalunit groupoperationalunit_pkey 
   CONSTRAINT     �   ALTER TABLE ONLY public.groupoperationalunit
    ADD CONSTRAINT groupoperationalunit_pkey PRIMARY KEY (group_id, operational_unit_id);
 X   ALTER TABLE ONLY public.groupoperationalunit DROP CONSTRAINT groupoperationalunit_pkey;
       public            qualicharge    false    284    284            �           2606    19866 -   localisation localisation_adresse_station_key 
   CONSTRAINT     s   ALTER TABLE ONLY public.localisation
    ADD CONSTRAINT localisation_adresse_station_key UNIQUE (adresse_station);
 W   ALTER TABLE ONLY public.localisation DROP CONSTRAINT localisation_adresse_station_key;
       public            qualicharge    false    275            �           2606    19762    localisation localisation_pkey 
   CONSTRAINT     \   ALTER TABLE ONLY public.localisation
    ADD CONSTRAINT localisation_pkey PRIMARY KEY (id);
 H   ALTER TABLE ONLY public.localisation DROP CONSTRAINT localisation_pkey;
       public            qualicharge    false    275            �           2606    19775 I   operateur operateur_nom_operateur_contact_operateur_telephone_operate_key 
   CONSTRAINT     �   ALTER TABLE ONLY public.operateur
    ADD CONSTRAINT operateur_nom_operateur_contact_operateur_telephone_operate_key UNIQUE (nom_operateur, contact_operateur, telephone_operateur);
 s   ALTER TABLE ONLY public.operateur DROP CONSTRAINT operateur_nom_operateur_contact_operateur_telephone_operate_key;
       public            qualicharge    false    276    276    276            �           2606    19773    operateur operateur_pkey 
   CONSTRAINT     V   ALTER TABLE ONLY public.operateur
    ADD CONSTRAINT operateur_pkey PRIMARY KEY (id);
 B   ALTER TABLE ONLY public.operateur DROP CONSTRAINT operateur_pkey;
       public            qualicharge    false    276            �           2606    19926 $   operationalunit operationalunit_pkey 
   CONSTRAINT     b   ALTER TABLE ONLY public.operationalunit
    ADD CONSTRAINT operationalunit_pkey PRIMARY KEY (id);
 N   ALTER TABLE ONLY public.operationalunit DROP CONSTRAINT operationalunit_pkey;
       public            qualicharge    false    281            �           2606    19844     pointdecharge pointdecharge_pkey 
   CONSTRAINT     ^   ALTER TABLE ONLY public.pointdecharge
    ADD CONSTRAINT pointdecharge_pkey PRIMARY KEY (id);
 J   ALTER TABLE ONLY public.pointdecharge DROP CONSTRAINT pointdecharge_pkey;
       public            qualicharge    false    278            �           2606    19872    session session_pkey 
   CONSTRAINT     R   ALTER TABLE ONLY public.session
    ADD CONSTRAINT session_pkey PRIMARY KEY (id);
 >   ALTER TABLE ONLY public.session DROP CONSTRAINT session_pkey;
       public            qualicharge    false    279            �           2606    19806    station station_pkey 
   CONSTRAINT     R   ALTER TABLE ONLY public.station
    ADD CONSTRAINT station_pkey PRIMARY KEY (id);
 >   ALTER TABLE ONLY public.station DROP CONSTRAINT station_pkey;
       public            qualicharge    false    277            �           2606    19908    status status_pkey 
   CONSTRAINT     P   ALTER TABLE ONLY public.status
    ADD CONSTRAINT status_pkey PRIMARY KEY (id);
 <   ALTER TABLE ONLY public.status DROP CONSTRAINT status_pkey;
       public            qualicharge    false    280            �           2606    19984    user user_email_key 
   CONSTRAINT     Q   ALTER TABLE ONLY public."user"
    ADD CONSTRAINT user_email_key UNIQUE (email);
 ?   ALTER TABLE ONLY public."user" DROP CONSTRAINT user_email_key;
       public            qualicharge    false    283            �           2606    19950    user user_pkey 
   CONSTRAINT     N   ALTER TABLE ONLY public."user"
    ADD CONSTRAINT user_pkey PRIMARY KEY (id);
 :   ALTER TABLE ONLY public."user" DROP CONSTRAINT user_pkey;
       public            qualicharge    false    283            �           2606    19952    user user_username_key 
   CONSTRAINT     W   ALTER TABLE ONLY public."user"
    ADD CONSTRAINT user_username_key UNIQUE (username);
 B   ALTER TABLE ONLY public."user" DROP CONSTRAINT user_username_key;
       public            qualicharge    false    283            �           2606    19972    usergroup usergroup_pkey 
   CONSTRAINT     e   ALTER TABLE ONLY public.usergroup
    ADD CONSTRAINT usergroup_pkey PRIMARY KEY (user_id, group_id);
 B   ALTER TABLE ONLY public.usergroup DROP CONSTRAINT usergroup_pkey;
       public            qualicharge    false    285    285            �           1259    21931    idx_city_geometry    INDEX     E   CREATE INDEX idx_city_geometry ON public.city USING gist (geometry);
 %   DROP INDEX public.idx_city_geometry;
       public            qualicharge    false    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    286            �           1259    23570    idx_department_geometry    INDEX     Q   CREATE INDEX idx_department_geometry ON public.department USING gist (geometry);
 +   DROP INDEX public.idx_department_geometry;
       public            qualicharge    false    287    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2            �           1259    23887    idx_epci_geometry    INDEX     E   CREATE INDEX idx_epci_geometry ON public.epci USING gist (geometry);
 %   DROP INDEX public.idx_epci_geometry;
       public            qualicharge    false    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    288            �           1259    19765    idx_localisation_coordonneesXY    INDEX     c   CREATE INDEX "idx_localisation_coordonneesXY" ON public.localisation USING gist ("coordonneesXY");
 4   DROP INDEX public."idx_localisation_coordonneesXY";
       public            qualicharge    false    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    275            �           1259    25724    idx_region_geometry    INDEX     I   CREATE INDEX idx_region_geometry ON public.region USING gist (geometry);
 '   DROP INDEX public.idx_region_geometry;
       public            qualicharge    false    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    289            �           1259    30046    ix_city_code    INDEX     D   CREATE UNIQUE INDEX ix_city_code ON public.city USING btree (code);
     DROP INDEX public.ix_city_code;
       public            qualicharge    false    286            �           1259    30780    ix_department_code    INDEX     P   CREATE UNIQUE INDEX ix_department_code ON public.department USING btree (code);
 &   DROP INDEX public.ix_department_code;
       public            qualicharge    false    287            �           1259    32025    ix_epci_code    INDEX     D   CREATE UNIQUE INDEX ix_epci_code ON public.epci USING btree (code);
     DROP INDEX public.ix_epci_code;
       public            qualicharge    false    288            �           1259    19927    ix_operationalunit_code    INDEX     Z   CREATE UNIQUE INDEX ix_operationalunit_code ON public.operationalunit USING btree (code);
 +   DROP INDEX public.ix_operationalunit_code;
       public            qualicharge    false    281            �           1259    20836 "   ix_pointdecharge_id_pdc_itinerance    INDEX     p   CREATE UNIQUE INDEX ix_pointdecharge_id_pdc_itinerance ON public.pointdecharge USING btree (id_pdc_itinerance);
 6   DROP INDEX public.ix_pointdecharge_id_pdc_itinerance;
       public            qualicharge    false    278            �           1259    32113    ix_region_code    INDEX     H   CREATE UNIQUE INDEX ix_region_code ON public.region USING btree (code);
 "   DROP INDEX public.ix_region_code;
       public            qualicharge    false    289            �           1259    19827     ix_station_id_station_itinerance    INDEX     l   CREATE UNIQUE INDEX ix_station_id_station_itinerance ON public.station USING btree (id_station_itinerance);
 4   DROP INDEX public.ix_station_id_station_itinerance;
       public            qualicharge    false    277            �           2606    19958 7   groupoperationalunit groupoperationalunit_group_id_fkey    FK CONSTRAINT     �   ALTER TABLE ONLY public.groupoperationalunit
    ADD CONSTRAINT groupoperationalunit_group_id_fkey FOREIGN KEY (group_id) REFERENCES public."group"(id);
 a   ALTER TABLE ONLY public.groupoperationalunit DROP CONSTRAINT groupoperationalunit_group_id_fkey;
       public          qualicharge    false    282    284    4833            �           2606    19963 B   groupoperationalunit groupoperationalunit_operational_unit_id_fkey    FK CONSTRAINT     �   ALTER TABLE ONLY public.groupoperationalunit
    ADD CONSTRAINT groupoperationalunit_operational_unit_id_fkey FOREIGN KEY (operational_unit_id) REFERENCES public.operationalunit(id);
 l   ALTER TABLE ONLY public.groupoperationalunit DROP CONSTRAINT groupoperationalunit_operational_unit_id_fkey;
       public          qualicharge    false    4829    281    284            �           2606    19845 +   pointdecharge pointdecharge_station_id_fkey    FK CONSTRAINT     �   ALTER TABLE ONLY public.pointdecharge
    ADD CONSTRAINT pointdecharge_station_id_fkey FOREIGN KEY (station_id) REFERENCES public.station(id);
 U   ALTER TABLE ONLY public.pointdecharge DROP CONSTRAINT pointdecharge_station_id_fkey;
       public          qualicharge    false    277    4819    278            �           2606    19873 '   session session_point_de_charge_id_fkey    FK CONSTRAINT     �   ALTER TABLE ONLY public.session
    ADD CONSTRAINT session_point_de_charge_id_fkey FOREIGN KEY (point_de_charge_id) REFERENCES public.pointdecharge(id);
 Q   ALTER TABLE ONLY public.session DROP CONSTRAINT session_point_de_charge_id_fkey;
       public          qualicharge    false    278    4822    279            �           2606    19807 !   station station_amenageur_id_fkey    FK CONSTRAINT     �   ALTER TABLE ONLY public.station
    ADD CONSTRAINT station_amenageur_id_fkey FOREIGN KEY (amenageur_id) REFERENCES public.amenageur(id);
 K   ALTER TABLE ONLY public.station DROP CONSTRAINT station_amenageur_id_fkey;
       public          qualicharge    false    277    4803    273            �           2606    19812     station station_enseigne_id_fkey    FK CONSTRAINT     �   ALTER TABLE ONLY public.station
    ADD CONSTRAINT station_enseigne_id_fkey FOREIGN KEY (enseigne_id) REFERENCES public.enseigne(id);
 J   ALTER TABLE ONLY public.station DROP CONSTRAINT station_enseigne_id_fkey;
       public          qualicharge    false    277    274    4807            �           2606    19817 $   station station_localisation_id_fkey    FK CONSTRAINT     �   ALTER TABLE ONLY public.station
    ADD CONSTRAINT station_localisation_id_fkey FOREIGN KEY (localisation_id) REFERENCES public.localisation(id);
 N   ALTER TABLE ONLY public.station DROP CONSTRAINT station_localisation_id_fkey;
       public          qualicharge    false    275    4812    277            �           2606    19822 !   station station_operateur_id_fkey    FK CONSTRAINT     �   ALTER TABLE ONLY public.station
    ADD CONSTRAINT station_operateur_id_fkey FOREIGN KEY (operateur_id) REFERENCES public.operateur(id);
 K   ALTER TABLE ONLY public.station DROP CONSTRAINT station_operateur_id_fkey;
       public          qualicharge    false    4816    276    277            �           2606    19928 (   station station_operational_unit_id_fkey    FK CONSTRAINT     �   ALTER TABLE ONLY public.station
    ADD CONSTRAINT station_operational_unit_id_fkey FOREIGN KEY (operational_unit_id) REFERENCES public.operationalunit(id);
 R   ALTER TABLE ONLY public.station DROP CONSTRAINT station_operational_unit_id_fkey;
       public          qualicharge    false    277    281    4829            �           2606    19909 %   status status_point_de_charge_id_fkey    FK CONSTRAINT     �   ALTER TABLE ONLY public.status
    ADD CONSTRAINT status_point_de_charge_id_fkey FOREIGN KEY (point_de_charge_id) REFERENCES public.pointdecharge(id);
 O   ALTER TABLE ONLY public.status DROP CONSTRAINT status_point_de_charge_id_fkey;
       public          qualicharge    false    4822    278    280            �           2606    19973 !   usergroup usergroup_group_id_fkey    FK CONSTRAINT     �   ALTER TABLE ONLY public.usergroup
    ADD CONSTRAINT usergroup_group_id_fkey FOREIGN KEY (group_id) REFERENCES public."group"(id);
 K   ALTER TABLE ONLY public.usergroup DROP CONSTRAINT usergroup_group_id_fkey;
       public          qualicharge    false    285    4833    282            �           2606    19978     usergroup usergroup_user_id_fkey    FK CONSTRAINT     �   ALTER TABLE ONLY public.usergroup
    ADD CONSTRAINT usergroup_user_id_fkey FOREIGN KEY (user_id) REFERENCES public."user"(id);
 J   ALTER TABLE ONLY public.usergroup DROP CONSTRAINT usergroup_user_id_fkey;
       public          qualicharge    false    285    4837    283           