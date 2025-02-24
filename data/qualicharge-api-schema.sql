PGDMP  	    9    *                }            qualicharge-api "   14.11 (Ubuntu 14.11-1.pgdg22.04+1) "   14.11 (Ubuntu 14.11-1.pgdg22.04+1) �    �           0    0    ENCODING    ENCODING        SET client_encoding = 'UTF8';
                      false            �           0    0 
   STDSTRINGS 
   STDSTRINGS     (   SET standard_conforming_strings = 'on';
                      false            �           0    0 
   SEARCHPATH 
   SEARCHPATH     8   SELECT pg_catalog.set_config('search_path', '', false);
                      false                        1262    16384    qualicharge-api    DATABASE     b   CREATE DATABASE "qualicharge-api" WITH TEMPLATE = template0 ENCODING = 'UTF8' LOCALE = 'C.UTF-8';
 !   DROP DATABASE "qualicharge-api";
                qualicharge    false                        3079    17796    timescaledb 	   EXTENSION     ?   CREATE EXTENSION IF NOT EXISTS timescaledb WITH SCHEMA public;
    DROP EXTENSION timescaledb;
                   false                       0    0    EXTENSION timescaledb    COMMENT     |   COMMENT ON EXTENSION timescaledb IS 'Enables scalable inserts and complex queries for time-series data (Apache 2 Edition)';
                        false    4                        3079    19579 
   btree_gist 	   EXTENSION     >   CREATE EXTENSION IF NOT EXISTS btree_gist WITH SCHEMA public;
    DROP EXTENSION btree_gist;
                   false                       0    0    EXTENSION btree_gist    COMMENT     T   COMMENT ON EXTENSION btree_gist IS 'support for indexing common datatypes in GiST';
                        false    3                        3079    18502    postgis 	   EXTENSION     ;   CREATE EXTENSION IF NOT EXISTS postgis WITH SCHEMA public;
    DROP EXTENSION postgis;
                   false                       0    0    EXTENSION postgis    COMMENT     ^   COMMENT ON EXTENSION postgis IS 'PostGIS geometry and geography spatial types and functions';
                        false    2            J	           1247    32767    accessibilite_pmr_enum    TYPE     �   CREATE TYPE public.accessibilite_pmr_enum AS ENUM (
    'Réservé PMR',
    'Accessible mais non réservé PMR',
    'Non accessible',
    'Accessibilité inconnue'
);
 )   DROP TYPE public.accessibilite_pmr_enum;
       public          qualicharge    false            D	           1247    32743    condition_acces_enum    TYPE     `   CREATE TYPE public.condition_acces_enum AS ENUM (
    'Accès libre',
    'Accès réservé'
);
 '   DROP TYPE public.condition_acces_enum;
       public          qualicharge    false            M	           1247    32783    etat_pdc_enum    TYPE     b   CREATE TYPE public.etat_pdc_enum AS ENUM (
    'en_service',
    'hors_service',
    'inconnu'
);
     DROP TYPE public.etat_pdc_enum;
       public          qualicharge    false            S	           1247    32812    etat_prise_enum    TYPE     e   CREATE TYPE public.etat_prise_enum AS ENUM (
    'fonctionnel',
    'hors_service',
    'inconnu'
);
 "   DROP TYPE public.etat_prise_enum;
       public          qualicharge    false            A	           1247    32725    implantation_station_enum    TYPE     �   CREATE TYPE public.implantation_station_enum AS ENUM (
    'Voirie',
    'Parking public',
    'Parking privé à usage public',
    'Parking privé réservé à la clientèle',
    'Station dédiée à la recharge rapide'
);
 ,   DROP TYPE public.implantation_station_enum;
       public          qualicharge    false            P	           1247    32796    occupation_pdc_enum    TYPE     l   CREATE TYPE public.occupation_pdc_enum AS ENUM (
    'libre',
    'occupe',
    'reserve',
    'inconnu'
);
 &   DROP TYPE public.occupation_pdc_enum;
       public          qualicharge    false            #	           1247    20397    operationalunittypeenum    TYPE     W   CREATE TYPE public.operationalunittypeenum AS ENUM (
    'CHARGING',
    'MOBILITY'
);
 *   DROP TYPE public.operationalunittypeenum;
       public          qualicharge    false            G	           1247    32755    raccordement_enum    TYPE     O   CREATE TYPE public.raccordement_enum AS ENUM (
    'Direct',
    'Indirect'
);
 $   DROP TYPE public.raccordement_enum;
       public          qualicharge    false            �           1255    32972    audit_table(regclass)    FUNCTION     �   CREATE FUNCTION public.audit_table(target_table regclass) RETURNS void
    LANGUAGE sql
    AS $$
SELECT audit_table(target_table, ARRAY[]::text[]);
$$;
 9   DROP FUNCTION public.audit_table(target_table regclass);
       public          qualicharge    false            �           1255    32971    audit_table(regclass, text[])    FUNCTION     "  CREATE FUNCTION public.audit_table(target_table regclass, ignored_cols text[]) RETURNS void
    LANGUAGE plpgsql
    AS $$
DECLARE
    query text;
    excluded_columns_text text = '';
BEGIN
    EXECUTE 'DROP TRIGGER IF EXISTS audit_trigger_insert ON ' || target_table;
    EXECUTE 'DROP TRIGGER IF EXISTS audit_trigger_update ON ' || target_table;
    EXECUTE 'DROP TRIGGER IF EXISTS audit_trigger_delete ON ' || target_table;

    IF array_length(ignored_cols, 1) > 0 THEN
        excluded_columns_text = ', ' || quote_literal(ignored_cols);
    END IF;
    query = 'CREATE TRIGGER audit_trigger_insert AFTER INSERT ON ' ||
             target_table || ' REFERENCING NEW TABLE AS new_table FOR EACH STATEMENT ' ||
             E'WHEN (get_setting(\'postgresql_audit.enable_versioning\', \'true\')::bool)' ||
             ' EXECUTE PROCEDURE create_activity(' ||
             excluded_columns_text ||
             ');';
    RAISE NOTICE '%', query;
    EXECUTE query;
    query = 'CREATE TRIGGER audit_trigger_update AFTER UPDATE ON ' ||
             target_table || ' REFERENCING NEW TABLE AS new_table OLD TABLE AS old_table FOR EACH STATEMENT ' ||
             E'WHEN (get_setting(\'postgresql_audit.enable_versioning\', \'true\')::bool)' ||
             ' EXECUTE PROCEDURE create_activity(' ||
             excluded_columns_text ||
             ');';
    RAISE NOTICE '%', query;
    EXECUTE query;
    query = 'CREATE TRIGGER audit_trigger_delete AFTER DELETE ON ' ||
             target_table || ' REFERENCING OLD TABLE AS old_table FOR EACH STATEMENT ' ||
             E'WHEN (get_setting(\'postgresql_audit.enable_versioning\', \'true\')::bool)' ||
             ' EXECUTE PROCEDURE create_activity(' ||
             excluded_columns_text ||
             ');';
    RAISE NOTICE '%', query;
    EXECUTE query;
END;
$$;
 N   DROP FUNCTION public.audit_table(target_table regclass, ignored_cols text[]);
       public          qualicharge    false            �           1255    32970    create_activity()    FUNCTION     #  CREATE FUNCTION public.create_activity() RETURNS trigger
    LANGUAGE plpgsql SECURITY DEFINER
    SET search_path TO 'pg_catalog', 'public'
    AS $$
DECLARE
    audit_row activity;
    excluded_cols text[] = ARRAY[]::text[];
    _transaction_id BIGINT;
BEGIN
    _transaction_id := (
        SELECT id
        FROM transaction
        WHERE
            native_transaction_id = txid_current() AND
            issued_at >= (NOW() - INTERVAL '1 day')
        ORDER BY issued_at DESC
        LIMIT 1
    );

    IF TG_ARGV[0] IS NOT NULL THEN
        excluded_cols = TG_ARGV[0]::text[];
    END IF;

    IF (TG_OP = 'UPDATE') THEN
        INSERT INTO activity(
            id, schema_name, table_name, relid, issued_at, native_transaction_id,
            verb, old_data, changed_data, transaction_id)
        SELECT
            nextval('activity_id_seq') as id,
            TG_TABLE_SCHEMA::text AS schema_name,
            TG_TABLE_NAME::text AS table_name,
            TG_RELID AS relid,
            statement_timestamp() AT TIME ZONE 'UTC' AS issued_at,
            txid_current() AS native_transaction_id,
            LOWER(TG_OP) AS verb,
            old_data - excluded_cols AS old_data,
            new_data - old_data - excluded_cols AS changed_data,
            _transaction_id AS transaction_id
        FROM (
            SELECT *
            FROM (
                SELECT
                    row_to_json(old_table.*)::jsonb AS old_data,
                    row_number() OVER ()
                FROM old_table
            ) AS old_table
            JOIN (
                SELECT
                    row_to_json(new_table.*)::jsonb AS new_data,
                    row_number() OVER ()
                FROM new_table
            ) AS new_table
            USING(row_number)
        ) as sub
        WHERE new_data - old_data - excluded_cols != '{}'::jsonb;
    ELSIF (TG_OP = 'INSERT') THEN
        INSERT INTO activity(
            id, schema_name, table_name, relid, issued_at, native_transaction_id,
            verb, old_data, changed_data, transaction_id)
        SELECT
            nextval('activity_id_seq') as id,
            TG_TABLE_SCHEMA::text AS schema_name,
            TG_TABLE_NAME::text AS table_name,
            TG_RELID AS relid,
            statement_timestamp() AT TIME ZONE 'UTC' AS issued_at,
            txid_current() AS native_transaction_id,
            LOWER(TG_OP) AS verb,
            '{}'::jsonb AS old_data,
            row_to_json(new_table.*)::jsonb - excluded_cols AS changed_data,
            _transaction_id AS transaction_id
        FROM new_table;
    ELSEIF TG_OP = 'DELETE' THEN
        INSERT INTO activity(
            id, schema_name, table_name, relid, issued_at, native_transaction_id,
            verb, old_data, changed_data, transaction_id)
        SELECT
            nextval('activity_id_seq') as id,
            TG_TABLE_SCHEMA::text AS schema_name,
            TG_TABLE_NAME::text AS table_name,
            TG_RELID AS relid,
            statement_timestamp() AT TIME ZONE 'UTC' AS issued_at,
            txid_current() AS native_transaction_id,
            LOWER(TG_OP) AS verb,
            row_to_json(old_table.*)::jsonb - excluded_cols AS old_data,
            '{}'::jsonb AS changed_data,
            _transaction_id AS transaction_id
        FROM old_table;
    END IF;
    RETURN NULL;
END;
$$;
 (   DROP FUNCTION public.create_activity();
       public          qualicharge    false            �           1255    32975    get_setting(text, text)    FUNCTION     �   CREATE FUNCTION public.get_setting(setting text, default_value text) RETURNS text
    LANGUAGE sql
    AS $$
    SELECT coalesce(
        nullif(current_setting(setting, 't'), ''),
        default_value
    );
$$;
 D   DROP FUNCTION public.get_setting(setting text, default_value text);
       public          qualicharge    false            �           1255    32969 (   jsonb_change_key_name(jsonb, text, text)    FUNCTION     E  CREATE FUNCTION public.jsonb_change_key_name(data jsonb, old_key text, new_key text) RETURNS jsonb
    LANGUAGE sql IMMUTABLE
    AS $$
    SELECT ('{'||string_agg(to_json(CASE WHEN key = old_key THEN new_key ELSE key END)||':'||value, ',')||'}')::jsonb
    FROM (
        SELECT *
        FROM jsonb_each(data)
    ) t;
$$;
 T   DROP FUNCTION public.jsonb_change_key_name(data jsonb, old_key text, new_key text);
       public          qualicharge    false            �           1255    32973    jsonb_subtract(jsonb, jsonb)    FUNCTION     �   CREATE FUNCTION public.jsonb_subtract(arg1 jsonb, arg2 jsonb) RETURNS jsonb
    LANGUAGE sql
    AS $$
SELECT
  COALESCE(json_object_agg(key, value), '{}')::jsonb
FROM
  jsonb_each(arg1)
WHERE
  (arg1 -> key) <> (arg2 -> key) OR (arg2 -> key) IS NULL
$$;
 =   DROP FUNCTION public.jsonb_subtract(arg1 jsonb, arg2 jsonb);
       public          qualicharge    false            �           2617    32974    -    OPERATOR     n   CREATE OPERATOR public.- (
    FUNCTION = public.jsonb_subtract,
    LEFTARG = jsonb,
    RIGHTARG = jsonb
);
 '   DROP OPERATOR public.- (jsonb, jsonb);
       public          qualicharge    false    1532            '           1259    32863    activity    TABLE     B  CREATE TABLE public.activity (
    id bigint NOT NULL,
    schema_name text,
    table_name text,
    relid integer,
    issued_at timestamp without time zone,
    native_transaction_id bigint,
    verb text,
    old_data jsonb DEFAULT '{}'::jsonb,
    changed_data jsonb DEFAULT '{}'::jsonb,
    transaction_id bigint
);
    DROP TABLE public.activity;
       public         heap    qualicharge    false            &           1259    32862    activity_id_seq    SEQUENCE     x   CREATE SEQUENCE public.activity_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;
 &   DROP SEQUENCE public.activity_id_seq;
       public          qualicharge    false    295                       0    0    activity_id_seq    SEQUENCE OWNED BY     C   ALTER SEQUENCE public.activity_id_seq OWNED BY public.activity.id;
          public          qualicharge    false    294                       1259    20211    alembic_version    TABLE     X   CREATE TABLE public.alembic_version (
    version_num character varying(32) NOT NULL
);
 #   DROP TABLE public.alembic_version;
       public         heap    qualicharge    false                       1259    20216 	   amenageur    TABLE     �  CREATE TABLE public.amenageur (
    created_at timestamp with time zone NOT NULL,
    updated_at timestamp with time zone NOT NULL,
    id uuid NOT NULL,
    nom_amenageur character varying,
    siren_amenageur character varying,
    contact_amenageur character varying,
    created_by_id uuid,
    updated_by_id uuid,
    CONSTRAINT "pre-creation-update" CHECK ((created_at <= updated_at))
);
    DROP TABLE public.amenageur;
       public         heap    qualicharge    false                       1259    23021    city    TABLE     t  CREATE TABLE public.city (
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
       public         heap    qualicharge    false    2    2    2    2    2    2    2    2                        1259    24660 
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
       public         heap    qualicharge    false    2    2    2    2    2    2    2    2                       1259    20226    enseigne    TABLE     A  CREATE TABLE public.enseigne (
    created_at timestamp with time zone NOT NULL,
    updated_at timestamp with time zone NOT NULL,
    id uuid NOT NULL,
    nom_enseigne character varying NOT NULL,
    created_by_id uuid,
    updated_by_id uuid,
    CONSTRAINT "pre-creation-update" CHECK ((created_at <= updated_at))
);
    DROP TABLE public.enseigne;
       public         heap    qualicharge    false            !           1259    24977    epci    TABLE     J  CREATE TABLE public.epci (
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
       public         heap    qualicharge    false    2    2    2    2    2    2    2    2                       1259    20415    group    TABLE     8  CREATE TABLE public."group" (
    created_at timestamp with time zone NOT NULL,
    updated_at timestamp with time zone NOT NULL,
    id uuid NOT NULL,
    name character varying NOT NULL,
    created_by_id uuid,
    updated_by_id uuid,
    CONSTRAINT "pre-creation-update" CHECK ((created_at <= updated_at))
);
    DROP TABLE public."group";
       public         heap    qualicharge    false                       1259    20435    groupoperationalunit    TABLE     p   CREATE TABLE public.groupoperationalunit (
    group_id uuid NOT NULL,
    operational_unit_id uuid NOT NULL
);
 (   DROP TABLE public.groupoperationalunit;
       public         heap    qualicharge    false                       1259    20236    localisation    TABLE     �  CREATE TABLE public.localisation (
    created_at timestamp with time zone NOT NULL,
    updated_at timestamp with time zone NOT NULL,
    id uuid NOT NULL,
    adresse_station character varying NOT NULL,
    code_insee_commune character varying NOT NULL,
    "coordonneesXY" public.geometry(Point,4326) NOT NULL,
    created_by_id uuid,
    updated_by_id uuid,
    CONSTRAINT "pre-creation-update" CHECK ((created_at <= updated_at))
);
     DROP TABLE public.localisation;
       public         heap    qualicharge    false    2    2    2    2    2    2    2    2                       1259    20247 	   operateur    TABLE     �  CREATE TABLE public.operateur (
    created_at timestamp with time zone NOT NULL,
    updated_at timestamp with time zone NOT NULL,
    id uuid NOT NULL,
    nom_operateur character varying,
    contact_operateur character varying NOT NULL,
    telephone_operateur character varying,
    created_by_id uuid,
    updated_by_id uuid,
    CONSTRAINT "pre-creation-update" CHECK ((created_at <= updated_at))
);
    DROP TABLE public.operateur;
       public         heap    qualicharge    false                       1259    20401    operationalunit    TABLE     g  CREATE TABLE public.operationalunit (
    created_at timestamp with time zone NOT NULL,
    updated_at timestamp with time zone NOT NULL,
    id uuid NOT NULL,
    code character varying NOT NULL,
    name character varying NOT NULL,
    type public.operationalunittypeenum NOT NULL,
    CONSTRAINT "pre-creation-update" CHECK ((created_at <= updated_at))
);
 #   DROP TABLE public.operationalunit;
       public         heap    qualicharge    false    2339                       1259    20319    pointdecharge    TABLE     �  CREATE TABLE public.pointdecharge (
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
    accessibilite_pmr public.accessibilite_pmr_enum NOT NULL,
    restriction_gabarit character varying NOT NULL,
    observations character varying,
    cable_t2_attache boolean,
    station_id uuid,
    created_by_id uuid,
    updated_by_id uuid,
    CONSTRAINT "pre-creation-update" CHECK ((created_at <= updated_at))
);
 !   DROP TABLE public.pointdecharge;
       public         heap    qualicharge    false    2378            "           1259    26814    region    TABLE     L  CREATE TABLE public.region (
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
       public         heap    qualicharge    false    2    2    2    2    2    2    2    2                       1259    20349    session    TABLE     �  CREATE TABLE public.session (
    energy double precision NOT NULL,
    created_at timestamp with time zone NOT NULL,
    updated_at timestamp with time zone NOT NULL,
    id uuid NOT NULL,
    start timestamp with time zone NOT NULL,
    "end" timestamp with time zone NOT NULL,
    point_de_charge_id uuid,
    created_by_id uuid,
    updated_by_id uuid,
    CONSTRAINT "pre-creation-update" CHECK ((created_at <= updated_at))
);
    DROP TABLE public.session;
       public         heap    qualicharge    false                       1259    20281    station    TABLE     �  CREATE TABLE public.station (
    created_at timestamp with time zone NOT NULL,
    updated_at timestamp with time zone NOT NULL,
    id uuid NOT NULL,
    id_station_itinerance character varying NOT NULL,
    id_station_local character varying,
    nom_station character varying NOT NULL,
    implantation_station public.implantation_station_enum NOT NULL,
    nbre_pdc integer NOT NULL,
    condition_acces public.condition_acces_enum NOT NULL,
    horaires character varying NOT NULL,
    station_deux_roues boolean NOT NULL,
    raccordement public.raccordement_enum,
    num_pdl character varying,
    date_maj date NOT NULL,
    date_mise_en_service date,
    amenageur_id uuid,
    operateur_id uuid,
    enseigne_id uuid,
    localisation_id uuid,
    operational_unit_id uuid,
    created_by_id uuid,
    updated_by_id uuid,
    CONSTRAINT "pre-creation-update" CHECK ((created_at <= updated_at))
);
    DROP TABLE public.station;
       public         heap    qualicharge    false    2372    2375    2369            #           1259    32841    statique    MATERIALIZED VIEW     7  CREATE MATERIALIZED VIEW public.statique AS
 SELECT pointdecharge.id AS pdc_id,
    pointdecharge.updated_at AS pdc_updated_at,
    amenageur.nom_amenageur,
    amenageur.siren_amenageur,
    amenageur.contact_amenageur,
    operateur.nom_operateur,
    operateur.contact_operateur,
    operateur.telephone_operateur,
    enseigne.nom_enseigne,
    station.id_station_itinerance,
    station.id_station_local,
    station.nom_station,
    station.implantation_station,
    localisation.adresse_station,
    localisation.code_insee_commune,
    public.st_asewkb(localisation."coordonneesXY") AS "coordonneesXY",
    station.nbre_pdc,
    pointdecharge.id_pdc_itinerance,
    pointdecharge.id_pdc_local,
    pointdecharge.puissance_nominale,
    pointdecharge.prise_type_ef,
    pointdecharge.prise_type_2,
    pointdecharge.prise_type_combo_ccs,
    pointdecharge.prise_type_chademo,
    pointdecharge.prise_type_autre,
    pointdecharge.gratuit,
    pointdecharge.paiement_acte,
    pointdecharge.paiement_cb,
    pointdecharge.paiement_autre,
    pointdecharge.tarification,
    station.condition_acces,
    pointdecharge.reservation,
    station.horaires,
    pointdecharge.accessibilite_pmr,
    pointdecharge.restriction_gabarit,
    station.station_deux_roues,
    station.raccordement,
    station.num_pdl,
    station.date_mise_en_service,
    pointdecharge.observations,
    station.date_maj,
    pointdecharge.cable_t2_attache
   FROM (((((public.pointdecharge
     JOIN public.station ON ((station.id = pointdecharge.station_id)))
     JOIN public.amenageur ON ((amenageur.id = station.amenageur_id)))
     JOIN public.operateur ON ((operateur.id = station.operateur_id)))
     JOIN public.enseigne ON ((enseigne.id = station.enseigne_id)))
     JOIN public.localisation ON ((localisation.id = station.localisation_id)))
  WITH NO DATA;
 (   DROP MATERIALIZED VIEW public.statique;
       public         heap    qualicharge    false    277    277    2    2    2    2    2    2    2    2    2    274    274    274    274    275    275    276    276    276    276    277    277    279    279    279    279    279    279    279    279    279    279    279    279    279    279    279    279    279    279    279    279    279    278    278    278    278    278    278    278    278    278    278    278    278    278    278    278    278    278    2372    2375    2378    2369                       1259    20385    status    TABLE     \  CREATE TABLE public.status (
    etat_pdc public.etat_pdc_enum NOT NULL,
    occupation_pdc public.occupation_pdc_enum NOT NULL,
    etat_prise_type_2 public.etat_prise_enum,
    etat_prise_type_combo_ccs public.etat_prise_enum,
    etat_prise_type_chademo public.etat_prise_enum,
    etat_prise_type_ef public.etat_prise_enum,
    created_at timestamp with time zone NOT NULL,
    updated_at timestamp with time zone NOT NULL,
    id uuid NOT NULL,
    horodatage timestamp with time zone NOT NULL,
    point_de_charge_id uuid,
    CONSTRAINT "pre-creation-update" CHECK ((created_at <= updated_at))
);
    DROP TABLE public.status;
       public         heap    qualicharge    false    2387    2387    2387    2384    2387    2381            %           1259    32852    transaction    TABLE     �   CREATE TABLE public.transaction (
    id bigint NOT NULL,
    native_transaction_id bigint,
    issued_at timestamp without time zone,
    client_addr inet,
    actor_id text
);
    DROP TABLE public.transaction;
       public         heap    qualicharge    false            $           1259    32851    transaction_id_seq    SEQUENCE     {   CREATE SEQUENCE public.transaction_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;
 )   DROP SEQUENCE public.transaction_id_seq;
       public          qualicharge    false    293                       0    0    transaction_id_seq    SEQUENCE OWNED BY     I   ALTER SEQUENCE public.transaction_id_seq OWNED BY public.transaction.id;
          public          qualicharge    false    292                       1259    20425    user    TABLE     �  CREATE TABLE public."user" (
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
    created_by_id uuid,
    updated_by_id uuid,
    CONSTRAINT "pre-creation-update" CHECK ((created_at <= updated_at))
);
    DROP TABLE public."user";
       public         heap    qualicharge    false                       1259    20450 	   usergroup    TABLE     Y   CREATE TABLE public.usergroup (
    user_id uuid NOT NULL,
    group_id uuid NOT NULL
);
    DROP TABLE public.usergroup;
       public         heap    qualicharge    false            �           2604    32866    activity id    DEFAULT     j   ALTER TABLE ONLY public.activity ALTER COLUMN id SET DEFAULT nextval('public.activity_id_seq'::regclass);
 :   ALTER TABLE public.activity ALTER COLUMN id DROP DEFAULT;
       public          qualicharge    false    294    295    295            �           2604    32855    transaction id    DEFAULT     p   ALTER TABLE ONLY public.transaction ALTER COLUMN id SET DEFAULT nextval('public.transaction_id_seq'::regclass);
 =   ALTER TABLE public.transaction ALTER COLUMN id DROP DEFAULT;
       public          qualicharge    false    292    293    293                       2606    32872    activity activity_pkey 
   CONSTRAINT     T   ALTER TABLE ONLY public.activity
    ADD CONSTRAINT activity_pkey PRIMARY KEY (id);
 @   ALTER TABLE ONLY public.activity DROP CONSTRAINT activity_pkey;
       public            qualicharge    false    295            �           2606    20215 #   alembic_version alembic_version_pkc 
   CONSTRAINT     j   ALTER TABLE ONLY public.alembic_version
    ADD CONSTRAINT alembic_version_pkc PRIMARY KEY (version_num);
 M   ALTER TABLE ONLY public.alembic_version DROP CONSTRAINT alembic_version_pkc;
       public            qualicharge    false    273            �           2606    20225 G   amenageur amenageur_nom_amenageur_siren_amenageur_contact_amenageur_key 
   CONSTRAINT     �   ALTER TABLE ONLY public.amenageur
    ADD CONSTRAINT amenageur_nom_amenageur_siren_amenageur_contact_amenageur_key UNIQUE (nom_amenageur, siren_amenageur, contact_amenageur);
 q   ALTER TABLE ONLY public.amenageur DROP CONSTRAINT amenageur_nom_amenageur_siren_amenageur_contact_amenageur_key;
       public            qualicharge    false    274    274    274            �           2606    20223    amenageur amenageur_pkey 
   CONSTRAINT     V   ALTER TABLE ONLY public.amenageur
    ADD CONSTRAINT amenageur_pkey PRIMARY KEY (id);
 B   ALTER TABLE ONLY public.amenageur DROP CONSTRAINT amenageur_pkey;
       public            qualicharge    false    274                       2606    32602    city city_pkey 
   CONSTRAINT     L   ALTER TABLE ONLY public.city
    ADD CONSTRAINT city_pkey PRIMARY KEY (id);
 8   ALTER TABLE ONLY public.city DROP CONSTRAINT city_pkey;
       public            qualicharge    false    287                       2606    32598    department department_pkey 
   CONSTRAINT     X   ALTER TABLE ONLY public.department
    ADD CONSTRAINT department_pkey PRIMARY KEY (id);
 D   ALTER TABLE ONLY public.department DROP CONSTRAINT department_pkey;
       public            qualicharge    false    288            �           2606    20235 "   enseigne enseigne_nom_enseigne_key 
   CONSTRAINT     e   ALTER TABLE ONLY public.enseigne
    ADD CONSTRAINT enseigne_nom_enseigne_key UNIQUE (nom_enseigne);
 L   ALTER TABLE ONLY public.enseigne DROP CONSTRAINT enseigne_nom_enseigne_key;
       public            qualicharge    false    275            �           2606    20233    enseigne enseigne_pkey 
   CONSTRAINT     T   ALTER TABLE ONLY public.enseigne
    ADD CONSTRAINT enseigne_pkey PRIMARY KEY (id);
 @   ALTER TABLE ONLY public.enseigne DROP CONSTRAINT enseigne_pkey;
       public            qualicharge    false    275                       2606    32600    epci epci_pkey 
   CONSTRAINT     L   ALTER TABLE ONLY public.epci
    ADD CONSTRAINT epci_pkey PRIMARY KEY (id);
 8   ALTER TABLE ONLY public.epci DROP CONSTRAINT epci_pkey;
       public            qualicharge    false    289            �           2606    20424    group group_name_key 
   CONSTRAINT     Q   ALTER TABLE ONLY public."group"
    ADD CONSTRAINT group_name_key UNIQUE (name);
 @   ALTER TABLE ONLY public."group" DROP CONSTRAINT group_name_key;
       public            qualicharge    false    283            �           2606    20422    group group_pkey 
   CONSTRAINT     P   ALTER TABLE ONLY public."group"
    ADD CONSTRAINT group_pkey PRIMARY KEY (id);
 <   ALTER TABLE ONLY public."group" DROP CONSTRAINT group_pkey;
       public            qualicharge    false    283                       2606    20439 .   groupoperationalunit groupoperationalunit_pkey 
   CONSTRAINT     �   ALTER TABLE ONLY public.groupoperationalunit
    ADD CONSTRAINT groupoperationalunit_pkey PRIMARY KEY (group_id, operational_unit_id);
 X   ALTER TABLE ONLY public.groupoperationalunit DROP CONSTRAINT groupoperationalunit_pkey;
       public            qualicharge    false    285    285            �           2606    32657 +   localisation localisation_coordonneesXY_key 
   CONSTRAINT     s   ALTER TABLE ONLY public.localisation
    ADD CONSTRAINT "localisation_coordonneesXY_key" UNIQUE ("coordonneesXY");
 W   ALTER TABLE ONLY public.localisation DROP CONSTRAINT "localisation_coordonneesXY_key";
       public            qualicharge    false    276            �           2606    20243    localisation localisation_pkey 
   CONSTRAINT     \   ALTER TABLE ONLY public.localisation
    ADD CONSTRAINT localisation_pkey PRIMARY KEY (id);
 H   ALTER TABLE ONLY public.localisation DROP CONSTRAINT localisation_pkey;
       public            qualicharge    false    276            �           2606    20256 I   operateur operateur_nom_operateur_contact_operateur_telephone_operate_key 
   CONSTRAINT     �   ALTER TABLE ONLY public.operateur
    ADD CONSTRAINT operateur_nom_operateur_contact_operateur_telephone_operate_key UNIQUE (nom_operateur, contact_operateur, telephone_operateur);
 s   ALTER TABLE ONLY public.operateur DROP CONSTRAINT operateur_nom_operateur_contact_operateur_telephone_operate_key;
       public            qualicharge    false    277    277    277            �           2606    20254    operateur operateur_pkey 
   CONSTRAINT     V   ALTER TABLE ONLY public.operateur
    ADD CONSTRAINT operateur_pkey PRIMARY KEY (id);
 B   ALTER TABLE ONLY public.operateur DROP CONSTRAINT operateur_pkey;
       public            qualicharge    false    277            �           2606    20408 $   operationalunit operationalunit_pkey 
   CONSTRAINT     b   ALTER TABLE ONLY public.operationalunit
    ADD CONSTRAINT operationalunit_pkey PRIMARY KEY (id);
 N   ALTER TABLE ONLY public.operationalunit DROP CONSTRAINT operationalunit_pkey;
       public            qualicharge    false    282            �           2606    20326     pointdecharge pointdecharge_pkey 
   CONSTRAINT     ^   ALTER TABLE ONLY public.pointdecharge
    ADD CONSTRAINT pointdecharge_pkey PRIMARY KEY (id);
 J   ALTER TABLE ONLY public.pointdecharge DROP CONSTRAINT pointdecharge_pkey;
       public            qualicharge    false    279                       2606    32596    region region_pkey 
   CONSTRAINT     P   ALTER TABLE ONLY public.region
    ADD CONSTRAINT region_pkey PRIMARY KEY (id);
 <   ALTER TABLE ONLY public.region DROP CONSTRAINT region_pkey;
       public            qualicharge    false    290            �           2606    20354    session session_pkey 
   CONSTRAINT     R   ALTER TABLE ONLY public.session
    ADD CONSTRAINT session_pkey PRIMARY KEY (id);
 >   ALTER TABLE ONLY public.session DROP CONSTRAINT session_pkey;
       public            qualicharge    false    280            �           2606    20288    station station_pkey 
   CONSTRAINT     R   ALTER TABLE ONLY public.station
    ADD CONSTRAINT station_pkey PRIMARY KEY (id);
 >   ALTER TABLE ONLY public.station DROP CONSTRAINT station_pkey;
       public            qualicharge    false    278            �           2606    20390    status status_pkey 
   CONSTRAINT     P   ALTER TABLE ONLY public.status
    ADD CONSTRAINT status_pkey PRIMARY KEY (id);
 <   ALTER TABLE ONLY public.status DROP CONSTRAINT status_pkey;
       public            qualicharge    false    281                       2606    32859    transaction transaction_pkey 
   CONSTRAINT     Z   ALTER TABLE ONLY public.transaction
    ADD CONSTRAINT transaction_pkey PRIMARY KEY (id);
 F   ALTER TABLE ONLY public.transaction DROP CONSTRAINT transaction_pkey;
       public            qualicharge    false    293                       2606    32861 +   transaction transaction_unique_native_tx_id 
   CONSTRAINT     �   ALTER TABLE ONLY public.transaction
    ADD CONSTRAINT transaction_unique_native_tx_id EXCLUDE USING gist (native_transaction_id WITH =, tsrange((issued_at - '01:00:00'::interval), issued_at) WITH &&);
 U   ALTER TABLE ONLY public.transaction DROP CONSTRAINT transaction_unique_native_tx_id;
       public            qualicharge    false    293            �           2606    20466    user user_email_key 
   CONSTRAINT     Q   ALTER TABLE ONLY public."user"
    ADD CONSTRAINT user_email_key UNIQUE (email);
 ?   ALTER TABLE ONLY public."user" DROP CONSTRAINT user_email_key;
       public            qualicharge    false    284            �           2606    20432    user user_pkey 
   CONSTRAINT     N   ALTER TABLE ONLY public."user"
    ADD CONSTRAINT user_pkey PRIMARY KEY (id);
 :   ALTER TABLE ONLY public."user" DROP CONSTRAINT user_pkey;
       public            qualicharge    false    284                       2606    20434    user user_username_key 
   CONSTRAINT     W   ALTER TABLE ONLY public."user"
    ADD CONSTRAINT user_username_key UNIQUE (username);
 B   ALTER TABLE ONLY public."user" DROP CONSTRAINT user_username_key;
       public            qualicharge    false    284                       2606    20454    usergroup usergroup_pkey 
   CONSTRAINT     e   ALTER TABLE ONLY public.usergroup
    ADD CONSTRAINT usergroup_pkey PRIMARY KEY (user_id, group_id);
 B   ALTER TABLE ONLY public.usergroup DROP CONSTRAINT usergroup_pkey;
       public            qualicharge    false    286    286                       1259    23026    idx_city_geometry    INDEX     E   CREATE INDEX idx_city_geometry ON public.city USING gist (geometry);
 %   DROP INDEX public.idx_city_geometry;
       public            qualicharge    false    287    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2                       1259    24665    idx_department_geometry    INDEX     Q   CREATE INDEX idx_department_geometry ON public.department USING gist (geometry);
 +   DROP INDEX public.idx_department_geometry;
       public            qualicharge    false    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    288                       1259    24982    idx_epci_geometry    INDEX     E   CREATE INDEX idx_epci_geometry ON public.epci USING gist (geometry);
 %   DROP INDEX public.idx_epci_geometry;
       public            qualicharge    false    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    289            �           1259    20246    idx_localisation_coordonneesXY    INDEX     c   CREATE INDEX "idx_localisation_coordonneesXY" ON public.localisation USING gist ("coordonneesXY");
 4   DROP INDEX public."idx_localisation_coordonneesXY";
       public            qualicharge    false    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    276                       1259    26819    idx_region_geometry    INDEX     I   CREATE INDEX idx_region_geometry ON public.region USING gist (geometry);
 '   DROP INDEX public.idx_region_geometry;
       public            qualicharge    false    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    290                       1259    32850    idx_statique_code_insee_commune    INDEX     b   CREATE INDEX idx_statique_code_insee_commune ON public.statique USING btree (code_insee_commune);
 3   DROP INDEX public.idx_statique_code_insee_commune;
       public            qualicharge    false    291                       1259    32848    idx_statique_coordonneesXY    INDEX     s   CREATE INDEX "idx_statique_coordonneesXY" ON public.statique USING gist (public.st_geomfromewkb("coordonneesXY"));
 0   DROP INDEX public."idx_statique_coordonneesXY";
       public            qualicharge    false    2    2    2    2    2    2    2    2    2    291    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    291                       1259    32849    idx_statique_id_pdc_itinerance    INDEX     g   CREATE UNIQUE INDEX idx_statique_id_pdc_itinerance ON public.statique USING btree (id_pdc_itinerance);
 2   DROP INDEX public.idx_statique_id_pdc_itinerance;
       public            qualicharge    false    291                       1259    32878 !   ix_activity_native_transaction_id    INDEX     g   CREATE INDEX ix_activity_native_transaction_id ON public.activity USING btree (native_transaction_id);
 5   DROP INDEX public.ix_activity_native_transaction_id;
       public            qualicharge    false    295            	           1259    30527    ix_city_code    INDEX     D   CREATE UNIQUE INDEX ix_city_code ON public.city USING btree (code);
     DROP INDEX public.ix_city_code;
       public            qualicharge    false    287                       1259    31261    ix_department_code    INDEX     P   CREATE UNIQUE INDEX ix_department_code ON public.department USING btree (code);
 &   DROP INDEX public.ix_department_code;
       public            qualicharge    false    288                       1259    32506    ix_epci_code    INDEX     D   CREATE UNIQUE INDEX ix_epci_code ON public.epci USING btree (code);
     DROP INDEX public.ix_epci_code;
       public            qualicharge    false    289            �           1259    20409    ix_operationalunit_code    INDEX     Z   CREATE UNIQUE INDEX ix_operationalunit_code ON public.operationalunit USING btree (code);
 +   DROP INDEX public.ix_operationalunit_code;
       public            qualicharge    false    282            �           1259    21307 "   ix_pointdecharge_id_pdc_itinerance    INDEX     p   CREATE UNIQUE INDEX ix_pointdecharge_id_pdc_itinerance ON public.pointdecharge USING btree (id_pdc_itinerance);
 6   DROP INDEX public.ix_pointdecharge_id_pdc_itinerance;
       public            qualicharge    false    279                       1259    32594    ix_region_code    INDEX     H   CREATE UNIQUE INDEX ix_region_code ON public.region USING btree (code);
 "   DROP INDEX public.ix_region_code;
       public            qualicharge    false    290            �           1259    20309     ix_station_id_station_itinerance    INDEX     l   CREATE UNIQUE INDEX ix_station_id_station_itinerance ON public.station USING btree (id_station_itinerance);
 4   DROP INDEX public.ix_station_id_station_itinerance;
       public            qualicharge    false    278            B           2620    32984    amenageur audit_trigger_delete    TRIGGER       CREATE TRIGGER audit_trigger_delete AFTER DELETE ON public.amenageur REFERENCING OLD TABLE AS old_table FOR EACH STATEMENT WHEN ((public.get_setting('postgresql_audit.enable_versioning'::text, 'true'::text))::boolean) EXECUTE FUNCTION public.create_activity('{created_at,updated_at}');
 7   DROP TRIGGER audit_trigger_delete ON public.amenageur;
       public          qualicharge    false    274    1529    1533            E           2620    32990    enseigne audit_trigger_delete    TRIGGER       CREATE TRIGGER audit_trigger_delete AFTER DELETE ON public.enseigne REFERENCING OLD TABLE AS old_table FOR EACH STATEMENT WHEN ((public.get_setting('postgresql_audit.enable_versioning'::text, 'true'::text))::boolean) EXECUTE FUNCTION public.create_activity('{created_at,updated_at}');
 6   DROP TRIGGER audit_trigger_delete ON public.enseigne;
       public          qualicharge    false    1533    1529    275            W           2620    32981    group audit_trigger_delete    TRIGGER       CREATE TRIGGER audit_trigger_delete AFTER DELETE ON public."group" REFERENCING OLD TABLE AS old_table FOR EACH STATEMENT WHEN ((public.get_setting('postgresql_audit.enable_versioning'::text, 'true'::text))::boolean) EXECUTE FUNCTION public.create_activity('{created_at,updated_at}');
 5   DROP TRIGGER audit_trigger_delete ON public."group";
       public          qualicharge    false    283    1529    1533            H           2620    32993 !   localisation audit_trigger_delete    TRIGGER     !  CREATE TRIGGER audit_trigger_delete AFTER DELETE ON public.localisation REFERENCING OLD TABLE AS old_table FOR EACH STATEMENT WHEN ((public.get_setting('postgresql_audit.enable_versioning'::text, 'true'::text))::boolean) EXECUTE FUNCTION public.create_activity('{created_at,updated_at}');
 :   DROP TRIGGER audit_trigger_delete ON public.localisation;
       public          qualicharge    false    276    1533    1529            K           2620    32987    operateur audit_trigger_delete    TRIGGER       CREATE TRIGGER audit_trigger_delete AFTER DELETE ON public.operateur REFERENCING OLD TABLE AS old_table FOR EACH STATEMENT WHEN ((public.get_setting('postgresql_audit.enable_versioning'::text, 'true'::text))::boolean) EXECUTE FUNCTION public.create_activity('{created_at,updated_at}');
 7   DROP TRIGGER audit_trigger_delete ON public.operateur;
       public          qualicharge    false    1529    1533    277            Q           2620    32999 "   pointdecharge audit_trigger_delete    TRIGGER     "  CREATE TRIGGER audit_trigger_delete AFTER DELETE ON public.pointdecharge REFERENCING OLD TABLE AS old_table FOR EACH STATEMENT WHEN ((public.get_setting('postgresql_audit.enable_versioning'::text, 'true'::text))::boolean) EXECUTE FUNCTION public.create_activity('{created_at,updated_at}');
 ;   DROP TRIGGER audit_trigger_delete ON public.pointdecharge;
       public          qualicharge    false    1533    279    1529            T           2620    33002    session audit_trigger_delete    TRIGGER       CREATE TRIGGER audit_trigger_delete AFTER DELETE ON public.session REFERENCING OLD TABLE AS old_table FOR EACH STATEMENT WHEN ((public.get_setting('postgresql_audit.enable_versioning'::text, 'true'::text))::boolean) EXECUTE FUNCTION public.create_activity('{created_at,updated_at}');
 5   DROP TRIGGER audit_trigger_delete ON public.session;
       public          qualicharge    false    1533    1529    280            N           2620    32996    station audit_trigger_delete    TRIGGER       CREATE TRIGGER audit_trigger_delete AFTER DELETE ON public.station REFERENCING OLD TABLE AS old_table FOR EACH STATEMENT WHEN ((public.get_setting('postgresql_audit.enable_versioning'::text, 'true'::text))::boolean) EXECUTE FUNCTION public.create_activity('{created_at,updated_at}');
 5   DROP TRIGGER audit_trigger_delete ON public.station;
       public          qualicharge    false    1533    278    1529            Z           2620    32978    user audit_trigger_delete    TRIGGER     $  CREATE TRIGGER audit_trigger_delete AFTER DELETE ON public."user" REFERENCING OLD TABLE AS old_table FOR EACH STATEMENT WHEN ((public.get_setting('postgresql_audit.enable_versioning'::text, 'true'::text))::boolean) EXECUTE FUNCTION public.create_activity('{created_at,updated_at,password}');
 4   DROP TRIGGER audit_trigger_delete ON public."user";
       public          qualicharge    false    1529    284    1533            C           2620    32982    amenageur audit_trigger_insert    TRIGGER       CREATE TRIGGER audit_trigger_insert AFTER INSERT ON public.amenageur REFERENCING NEW TABLE AS new_table FOR EACH STATEMENT WHEN ((public.get_setting('postgresql_audit.enable_versioning'::text, 'true'::text))::boolean) EXECUTE FUNCTION public.create_activity('{created_at,updated_at}');
 7   DROP TRIGGER audit_trigger_insert ON public.amenageur;
       public          qualicharge    false    1529    1533    274            F           2620    32988    enseigne audit_trigger_insert    TRIGGER       CREATE TRIGGER audit_trigger_insert AFTER INSERT ON public.enseigne REFERENCING NEW TABLE AS new_table FOR EACH STATEMENT WHEN ((public.get_setting('postgresql_audit.enable_versioning'::text, 'true'::text))::boolean) EXECUTE FUNCTION public.create_activity('{created_at,updated_at}');
 6   DROP TRIGGER audit_trigger_insert ON public.enseigne;
       public          qualicharge    false    1529    1533    275            X           2620    32979    group audit_trigger_insert    TRIGGER       CREATE TRIGGER audit_trigger_insert AFTER INSERT ON public."group" REFERENCING NEW TABLE AS new_table FOR EACH STATEMENT WHEN ((public.get_setting('postgresql_audit.enable_versioning'::text, 'true'::text))::boolean) EXECUTE FUNCTION public.create_activity('{created_at,updated_at}');
 5   DROP TRIGGER audit_trigger_insert ON public."group";
       public          qualicharge    false    1529    283    1533            I           2620    32991 !   localisation audit_trigger_insert    TRIGGER     !  CREATE TRIGGER audit_trigger_insert AFTER INSERT ON public.localisation REFERENCING NEW TABLE AS new_table FOR EACH STATEMENT WHEN ((public.get_setting('postgresql_audit.enable_versioning'::text, 'true'::text))::boolean) EXECUTE FUNCTION public.create_activity('{created_at,updated_at}');
 :   DROP TRIGGER audit_trigger_insert ON public.localisation;
       public          qualicharge    false    1533    276    1529            L           2620    32985    operateur audit_trigger_insert    TRIGGER       CREATE TRIGGER audit_trigger_insert AFTER INSERT ON public.operateur REFERENCING NEW TABLE AS new_table FOR EACH STATEMENT WHEN ((public.get_setting('postgresql_audit.enable_versioning'::text, 'true'::text))::boolean) EXECUTE FUNCTION public.create_activity('{created_at,updated_at}');
 7   DROP TRIGGER audit_trigger_insert ON public.operateur;
       public          qualicharge    false    277    1533    1529            R           2620    32997 "   pointdecharge audit_trigger_insert    TRIGGER     "  CREATE TRIGGER audit_trigger_insert AFTER INSERT ON public.pointdecharge REFERENCING NEW TABLE AS new_table FOR EACH STATEMENT WHEN ((public.get_setting('postgresql_audit.enable_versioning'::text, 'true'::text))::boolean) EXECUTE FUNCTION public.create_activity('{created_at,updated_at}');
 ;   DROP TRIGGER audit_trigger_insert ON public.pointdecharge;
       public          qualicharge    false    1529    1533    279            U           2620    33000    session audit_trigger_insert    TRIGGER       CREATE TRIGGER audit_trigger_insert AFTER INSERT ON public.session REFERENCING NEW TABLE AS new_table FOR EACH STATEMENT WHEN ((public.get_setting('postgresql_audit.enable_versioning'::text, 'true'::text))::boolean) EXECUTE FUNCTION public.create_activity('{created_at,updated_at}');
 5   DROP TRIGGER audit_trigger_insert ON public.session;
       public          qualicharge    false    1529    1533    280            O           2620    32994    station audit_trigger_insert    TRIGGER       CREATE TRIGGER audit_trigger_insert AFTER INSERT ON public.station REFERENCING NEW TABLE AS new_table FOR EACH STATEMENT WHEN ((public.get_setting('postgresql_audit.enable_versioning'::text, 'true'::text))::boolean) EXECUTE FUNCTION public.create_activity('{created_at,updated_at}');
 5   DROP TRIGGER audit_trigger_insert ON public.station;
       public          qualicharge    false    278    1529    1533            [           2620    32976    user audit_trigger_insert    TRIGGER     $  CREATE TRIGGER audit_trigger_insert AFTER INSERT ON public."user" REFERENCING NEW TABLE AS new_table FOR EACH STATEMENT WHEN ((public.get_setting('postgresql_audit.enable_versioning'::text, 'true'::text))::boolean) EXECUTE FUNCTION public.create_activity('{created_at,updated_at,password}');
 4   DROP TRIGGER audit_trigger_insert ON public."user";
       public          qualicharge    false    1529    284    1533            D           2620    32983    amenageur audit_trigger_update    TRIGGER     5  CREATE TRIGGER audit_trigger_update AFTER UPDATE ON public.amenageur REFERENCING OLD TABLE AS old_table NEW TABLE AS new_table FOR EACH STATEMENT WHEN ((public.get_setting('postgresql_audit.enable_versioning'::text, 'true'::text))::boolean) EXECUTE FUNCTION public.create_activity('{created_at,updated_at}');
 7   DROP TRIGGER audit_trigger_update ON public.amenageur;
       public          qualicharge    false    1533    274    1529            G           2620    32989    enseigne audit_trigger_update    TRIGGER     4  CREATE TRIGGER audit_trigger_update AFTER UPDATE ON public.enseigne REFERENCING OLD TABLE AS old_table NEW TABLE AS new_table FOR EACH STATEMENT WHEN ((public.get_setting('postgresql_audit.enable_versioning'::text, 'true'::text))::boolean) EXECUTE FUNCTION public.create_activity('{created_at,updated_at}');
 6   DROP TRIGGER audit_trigger_update ON public.enseigne;
       public          qualicharge    false    1529    1533    275            Y           2620    32980    group audit_trigger_update    TRIGGER     3  CREATE TRIGGER audit_trigger_update AFTER UPDATE ON public."group" REFERENCING OLD TABLE AS old_table NEW TABLE AS new_table FOR EACH STATEMENT WHEN ((public.get_setting('postgresql_audit.enable_versioning'::text, 'true'::text))::boolean) EXECUTE FUNCTION public.create_activity('{created_at,updated_at}');
 5   DROP TRIGGER audit_trigger_update ON public."group";
       public          qualicharge    false    1529    283    1533            J           2620    32992 !   localisation audit_trigger_update    TRIGGER     8  CREATE TRIGGER audit_trigger_update AFTER UPDATE ON public.localisation REFERENCING OLD TABLE AS old_table NEW TABLE AS new_table FOR EACH STATEMENT WHEN ((public.get_setting('postgresql_audit.enable_versioning'::text, 'true'::text))::boolean) EXECUTE FUNCTION public.create_activity('{created_at,updated_at}');
 :   DROP TRIGGER audit_trigger_update ON public.localisation;
       public          qualicharge    false    276    1529    1533            M           2620    32986    operateur audit_trigger_update    TRIGGER     5  CREATE TRIGGER audit_trigger_update AFTER UPDATE ON public.operateur REFERENCING OLD TABLE AS old_table NEW TABLE AS new_table FOR EACH STATEMENT WHEN ((public.get_setting('postgresql_audit.enable_versioning'::text, 'true'::text))::boolean) EXECUTE FUNCTION public.create_activity('{created_at,updated_at}');
 7   DROP TRIGGER audit_trigger_update ON public.operateur;
       public          qualicharge    false    277    1533    1529            S           2620    32998 "   pointdecharge audit_trigger_update    TRIGGER     9  CREATE TRIGGER audit_trigger_update AFTER UPDATE ON public.pointdecharge REFERENCING OLD TABLE AS old_table NEW TABLE AS new_table FOR EACH STATEMENT WHEN ((public.get_setting('postgresql_audit.enable_versioning'::text, 'true'::text))::boolean) EXECUTE FUNCTION public.create_activity('{created_at,updated_at}');
 ;   DROP TRIGGER audit_trigger_update ON public.pointdecharge;
       public          qualicharge    false    1529    1533    279            V           2620    33001    session audit_trigger_update    TRIGGER     3  CREATE TRIGGER audit_trigger_update AFTER UPDATE ON public.session REFERENCING OLD TABLE AS old_table NEW TABLE AS new_table FOR EACH STATEMENT WHEN ((public.get_setting('postgresql_audit.enable_versioning'::text, 'true'::text))::boolean) EXECUTE FUNCTION public.create_activity('{created_at,updated_at}');
 5   DROP TRIGGER audit_trigger_update ON public.session;
       public          qualicharge    false    280    1533    1529            P           2620    32995    station audit_trigger_update    TRIGGER     3  CREATE TRIGGER audit_trigger_update AFTER UPDATE ON public.station REFERENCING OLD TABLE AS old_table NEW TABLE AS new_table FOR EACH STATEMENT WHEN ((public.get_setting('postgresql_audit.enable_versioning'::text, 'true'::text))::boolean) EXECUTE FUNCTION public.create_activity('{created_at,updated_at}');
 5   DROP TRIGGER audit_trigger_update ON public.station;
       public          qualicharge    false    1533    1529    278            \           2620    32977    user audit_trigger_update    TRIGGER     ;  CREATE TRIGGER audit_trigger_update AFTER UPDATE ON public."user" REFERENCING OLD TABLE AS old_table NEW TABLE AS new_table FOR EACH STATEMENT WHEN ((public.get_setting('postgresql_audit.enable_versioning'::text, 'true'::text))::boolean) EXECUTE FUNCTION public.create_activity('{created_at,updated_at,password}');
 4   DROP TRIGGER audit_trigger_update ON public."user";
       public          qualicharge    false    1529    284    1533            A           2606    32873 %   activity activity_transaction_id_fkey    FK CONSTRAINT     �   ALTER TABLE ONLY public.activity
    ADD CONSTRAINT activity_transaction_id_fkey FOREIGN KEY (transaction_id) REFERENCES public.transaction(id);
 O   ALTER TABLE ONLY public.activity DROP CONSTRAINT activity_transaction_id_fkey;
       public          qualicharge    false    295    5146    293                        2606    32879 &   amenageur amenageur_created_by_id_fkey    FK CONSTRAINT     �   ALTER TABLE ONLY public.amenageur
    ADD CONSTRAINT amenageur_created_by_id_fkey FOREIGN KEY (created_by_id) REFERENCES public."user"(id);
 P   ALTER TABLE ONLY public.amenageur DROP CONSTRAINT amenageur_created_by_id_fkey;
       public          qualicharge    false    274    5119    284            !           2606    32884 &   amenageur amenageur_updated_by_id_fkey    FK CONSTRAINT     �   ALTER TABLE ONLY public.amenageur
    ADD CONSTRAINT amenageur_updated_by_id_fkey FOREIGN KEY (updated_by_id) REFERENCES public."user"(id);
 P   ALTER TABLE ONLY public.amenageur DROP CONSTRAINT amenageur_updated_by_id_fkey;
       public          qualicharge    false    274    5119    284            >           2606    32603    city city_department_id_fkey    FK CONSTRAINT     �   ALTER TABLE ONLY public.city
    ADD CONSTRAINT city_department_id_fkey FOREIGN KEY (department_id) REFERENCES public.department(id);
 F   ALTER TABLE ONLY public.city DROP CONSTRAINT city_department_id_fkey;
       public          qualicharge    false    288    287    5131            ?           2606    32608    city city_epci_id_fkey    FK CONSTRAINT     t   ALTER TABLE ONLY public.city
    ADD CONSTRAINT city_epci_id_fkey FOREIGN KEY (epci_id) REFERENCES public.epci(id);
 @   ALTER TABLE ONLY public.city DROP CONSTRAINT city_epci_id_fkey;
       public          qualicharge    false    289    5135    287            @           2606    32613 $   department department_region_id_fkey    FK CONSTRAINT     �   ALTER TABLE ONLY public.department
    ADD CONSTRAINT department_region_id_fkey FOREIGN KEY (region_id) REFERENCES public.region(id);
 N   ALTER TABLE ONLY public.department DROP CONSTRAINT department_region_id_fkey;
       public          qualicharge    false    288    290    5141            "           2606    32889 $   enseigne enseigne_created_by_id_fkey    FK CONSTRAINT     �   ALTER TABLE ONLY public.enseigne
    ADD CONSTRAINT enseigne_created_by_id_fkey FOREIGN KEY (created_by_id) REFERENCES public."user"(id);
 N   ALTER TABLE ONLY public.enseigne DROP CONSTRAINT enseigne_created_by_id_fkey;
       public          qualicharge    false    275    5119    284            #           2606    32894 $   enseigne enseigne_updated_by_id_fkey    FK CONSTRAINT     �   ALTER TABLE ONLY public.enseigne
    ADD CONSTRAINT enseigne_updated_by_id_fkey FOREIGN KEY (updated_by_id) REFERENCES public."user"(id);
 N   ALTER TABLE ONLY public.enseigne DROP CONSTRAINT enseigne_updated_by_id_fkey;
       public          qualicharge    false    284    5119    275            6           2606    32899    group group_created_by_id_fkey    FK CONSTRAINT     �   ALTER TABLE ONLY public."group"
    ADD CONSTRAINT group_created_by_id_fkey FOREIGN KEY (created_by_id) REFERENCES public."user"(id);
 J   ALTER TABLE ONLY public."group" DROP CONSTRAINT group_created_by_id_fkey;
       public          qualicharge    false    5119    284    283            7           2606    32904    group group_updated_by_id_fkey    FK CONSTRAINT     �   ALTER TABLE ONLY public."group"
    ADD CONSTRAINT group_updated_by_id_fkey FOREIGN KEY (updated_by_id) REFERENCES public."user"(id);
 J   ALTER TABLE ONLY public."group" DROP CONSTRAINT group_updated_by_id_fkey;
       public          qualicharge    false    5119    283    284            :           2606    20440 7   groupoperationalunit groupoperationalunit_group_id_fkey    FK CONSTRAINT     �   ALTER TABLE ONLY public.groupoperationalunit
    ADD CONSTRAINT groupoperationalunit_group_id_fkey FOREIGN KEY (group_id) REFERENCES public."group"(id);
 a   ALTER TABLE ONLY public.groupoperationalunit DROP CONSTRAINT groupoperationalunit_group_id_fkey;
       public          qualicharge    false    5115    283    285            ;           2606    20445 B   groupoperationalunit groupoperationalunit_operational_unit_id_fkey    FK CONSTRAINT     �   ALTER TABLE ONLY public.groupoperationalunit
    ADD CONSTRAINT groupoperationalunit_operational_unit_id_fkey FOREIGN KEY (operational_unit_id) REFERENCES public.operationalunit(id);
 l   ALTER TABLE ONLY public.groupoperationalunit DROP CONSTRAINT groupoperationalunit_operational_unit_id_fkey;
       public          qualicharge    false    282    285    5111            $           2606    32909 ,   localisation localisation_created_by_id_fkey    FK CONSTRAINT     �   ALTER TABLE ONLY public.localisation
    ADD CONSTRAINT localisation_created_by_id_fkey FOREIGN KEY (created_by_id) REFERENCES public."user"(id);
 V   ALTER TABLE ONLY public.localisation DROP CONSTRAINT localisation_created_by_id_fkey;
       public          qualicharge    false    284    276    5119            %           2606    32914 ,   localisation localisation_updated_by_id_fkey    FK CONSTRAINT     �   ALTER TABLE ONLY public.localisation
    ADD CONSTRAINT localisation_updated_by_id_fkey FOREIGN KEY (updated_by_id) REFERENCES public."user"(id);
 V   ALTER TABLE ONLY public.localisation DROP CONSTRAINT localisation_updated_by_id_fkey;
       public          qualicharge    false    284    276    5119            &           2606    32919 &   operateur operateur_created_by_id_fkey    FK CONSTRAINT     �   ALTER TABLE ONLY public.operateur
    ADD CONSTRAINT operateur_created_by_id_fkey FOREIGN KEY (created_by_id) REFERENCES public."user"(id);
 P   ALTER TABLE ONLY public.operateur DROP CONSTRAINT operateur_created_by_id_fkey;
       public          qualicharge    false    5119    277    284            '           2606    32924 &   operateur operateur_updated_by_id_fkey    FK CONSTRAINT     �   ALTER TABLE ONLY public.operateur
    ADD CONSTRAINT operateur_updated_by_id_fkey FOREIGN KEY (updated_by_id) REFERENCES public."user"(id);
 P   ALTER TABLE ONLY public.operateur DROP CONSTRAINT operateur_updated_by_id_fkey;
       public          qualicharge    false    5119    284    277            /           2606    32929 .   pointdecharge pointdecharge_created_by_id_fkey    FK CONSTRAINT     �   ALTER TABLE ONLY public.pointdecharge
    ADD CONSTRAINT pointdecharge_created_by_id_fkey FOREIGN KEY (created_by_id) REFERENCES public."user"(id);
 X   ALTER TABLE ONLY public.pointdecharge DROP CONSTRAINT pointdecharge_created_by_id_fkey;
       public          qualicharge    false    279    5119    284            0           2606    20327 +   pointdecharge pointdecharge_station_id_fkey    FK CONSTRAINT     �   ALTER TABLE ONLY public.pointdecharge
    ADD CONSTRAINT pointdecharge_station_id_fkey FOREIGN KEY (station_id) REFERENCES public.station(id);
 U   ALTER TABLE ONLY public.pointdecharge DROP CONSTRAINT pointdecharge_station_id_fkey;
       public          qualicharge    false    5101    278    279            1           2606    32934 .   pointdecharge pointdecharge_updated_by_id_fkey    FK CONSTRAINT     �   ALTER TABLE ONLY public.pointdecharge
    ADD CONSTRAINT pointdecharge_updated_by_id_fkey FOREIGN KEY (updated_by_id) REFERENCES public."user"(id);
 X   ALTER TABLE ONLY public.pointdecharge DROP CONSTRAINT pointdecharge_updated_by_id_fkey;
       public          qualicharge    false    279    284    5119            2           2606    32939 "   session session_created_by_id_fkey    FK CONSTRAINT     �   ALTER TABLE ONLY public.session
    ADD CONSTRAINT session_created_by_id_fkey FOREIGN KEY (created_by_id) REFERENCES public."user"(id);
 L   ALTER TABLE ONLY public.session DROP CONSTRAINT session_created_by_id_fkey;
       public          qualicharge    false    284    5119    280            3           2606    20355 '   session session_point_de_charge_id_fkey    FK CONSTRAINT     �   ALTER TABLE ONLY public.session
    ADD CONSTRAINT session_point_de_charge_id_fkey FOREIGN KEY (point_de_charge_id) REFERENCES public.pointdecharge(id);
 Q   ALTER TABLE ONLY public.session DROP CONSTRAINT session_point_de_charge_id_fkey;
       public          qualicharge    false    5104    280    279            4           2606    32944 "   session session_updated_by_id_fkey    FK CONSTRAINT     �   ALTER TABLE ONLY public.session
    ADD CONSTRAINT session_updated_by_id_fkey FOREIGN KEY (updated_by_id) REFERENCES public."user"(id);
 L   ALTER TABLE ONLY public.session DROP CONSTRAINT session_updated_by_id_fkey;
       public          qualicharge    false    5119    280    284            (           2606    32623 !   station station_amenageur_id_fkey    FK CONSTRAINT     �   ALTER TABLE ONLY public.station
    ADD CONSTRAINT station_amenageur_id_fkey FOREIGN KEY (amenageur_id) REFERENCES public.amenageur(id) ON DELETE SET NULL;
 K   ALTER TABLE ONLY public.station DROP CONSTRAINT station_amenageur_id_fkey;
       public          qualicharge    false    274    5085    278            )           2606    32949 "   station station_created_by_id_fkey    FK CONSTRAINT     �   ALTER TABLE ONLY public.station
    ADD CONSTRAINT station_created_by_id_fkey FOREIGN KEY (created_by_id) REFERENCES public."user"(id);
 L   ALTER TABLE ONLY public.station DROP CONSTRAINT station_created_by_id_fkey;
       public          qualicharge    false    284    278    5119            *           2606    32633     station station_enseigne_id_fkey    FK CONSTRAINT     �   ALTER TABLE ONLY public.station
    ADD CONSTRAINT station_enseigne_id_fkey FOREIGN KEY (enseigne_id) REFERENCES public.enseigne(id) ON DELETE SET NULL;
 J   ALTER TABLE ONLY public.station DROP CONSTRAINT station_enseigne_id_fkey;
       public          qualicharge    false    278    5089    275            +           2606    32638 $   station station_localisation_id_fkey    FK CONSTRAINT     �   ALTER TABLE ONLY public.station
    ADD CONSTRAINT station_localisation_id_fkey FOREIGN KEY (localisation_id) REFERENCES public.localisation(id) ON DELETE SET NULL;
 N   ALTER TABLE ONLY public.station DROP CONSTRAINT station_localisation_id_fkey;
       public          qualicharge    false    276    278    5094            ,           2606    32618 !   station station_operateur_id_fkey    FK CONSTRAINT     �   ALTER TABLE ONLY public.station
    ADD CONSTRAINT station_operateur_id_fkey FOREIGN KEY (operateur_id) REFERENCES public.operateur(id) ON DELETE SET NULL;
 K   ALTER TABLE ONLY public.station DROP CONSTRAINT station_operateur_id_fkey;
       public          qualicharge    false    277    5098    278            -           2606    32628 (   station station_operational_unit_id_fkey    FK CONSTRAINT     �   ALTER TABLE ONLY public.station
    ADD CONSTRAINT station_operational_unit_id_fkey FOREIGN KEY (operational_unit_id) REFERENCES public.operationalunit(id) ON DELETE SET NULL;
 R   ALTER TABLE ONLY public.station DROP CONSTRAINT station_operational_unit_id_fkey;
       public          qualicharge    false    282    5111    278            .           2606    32954 "   station station_updated_by_id_fkey    FK CONSTRAINT     �   ALTER TABLE ONLY public.station
    ADD CONSTRAINT station_updated_by_id_fkey FOREIGN KEY (updated_by_id) REFERENCES public."user"(id);
 L   ALTER TABLE ONLY public.station DROP CONSTRAINT station_updated_by_id_fkey;
       public          qualicharge    false    278    5119    284            5           2606    20391 %   status status_point_de_charge_id_fkey    FK CONSTRAINT     �   ALTER TABLE ONLY public.status
    ADD CONSTRAINT status_point_de_charge_id_fkey FOREIGN KEY (point_de_charge_id) REFERENCES public.pointdecharge(id);
 O   ALTER TABLE ONLY public.status DROP CONSTRAINT status_point_de_charge_id_fkey;
       public          qualicharge    false    279    5104    281            8           2606    32959    user user_created_by_id_fkey    FK CONSTRAINT     �   ALTER TABLE ONLY public."user"
    ADD CONSTRAINT user_created_by_id_fkey FOREIGN KEY (created_by_id) REFERENCES public."user"(id);
 H   ALTER TABLE ONLY public."user" DROP CONSTRAINT user_created_by_id_fkey;
       public          qualicharge    false    284    284    5119            9           2606    32964    user user_updated_by_id_fkey    FK CONSTRAINT     �   ALTER TABLE ONLY public."user"
    ADD CONSTRAINT user_updated_by_id_fkey FOREIGN KEY (updated_by_id) REFERENCES public."user"(id);
 H   ALTER TABLE ONLY public."user" DROP CONSTRAINT user_updated_by_id_fkey;
       public          qualicharge    false    284    5119    284            <           2606    20455 !   usergroup usergroup_group_id_fkey    FK CONSTRAINT     �   ALTER TABLE ONLY public.usergroup
    ADD CONSTRAINT usergroup_group_id_fkey FOREIGN KEY (group_id) REFERENCES public."group"(id);
 K   ALTER TABLE ONLY public.usergroup DROP CONSTRAINT usergroup_group_id_fkey;
       public          qualicharge    false    5115    286    283            =           2606    20460     usergroup usergroup_user_id_fkey    FK CONSTRAINT     �   ALTER TABLE ONLY public.usergroup
    ADD CONSTRAINT usergroup_user_id_fkey FOREIGN KEY (user_id) REFERENCES public."user"(id);
 J   ALTER TABLE ONLY public.usergroup DROP CONSTRAINT usergroup_user_id_fkey;
       public          qualicharge    false    284    286    5119           