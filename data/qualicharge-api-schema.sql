PGDMP  	        1                }            qualicharge-api "   15.12 (Ubuntu 15.12-1.pgdg22.04+1) "   15.12 (Ubuntu 15.12-1.pgdg22.04+1)    (           0    0    ENCODING    ENCODING        SET client_encoding = 'UTF8';
                      false            )           0    0 
   STDSTRINGS 
   STDSTRINGS     (   SET standard_conforming_strings = 'on';
                      false            *           0    0 
   SEARCHPATH 
   SEARCHPATH     8   SELECT pg_catalog.set_config('search_path', '', false);
                      false            +           1262    16384    qualicharge-api    DATABASE     y   CREATE DATABASE "qualicharge-api" WITH TEMPLATE = template0 ENCODING = 'UTF8' LOCALE_PROVIDER = libc LOCALE = 'C.UTF-8';
 !   DROP DATABASE "qualicharge-api";
                qualicharge    false                        3079    17891    timescaledb 	   EXTENSION     ?   CREATE EXTENSION IF NOT EXISTS timescaledb WITH SCHEMA public;
    DROP EXTENSION timescaledb;
                   false            ,           0    0    EXTENSION timescaledb    COMMENT     |   COMMENT ON EXTENSION timescaledb IS 'Enables scalable inserts and complex queries for time-series data (Apache 2 Edition)';
                        false    4                        3079    19741 
   btree_gist 	   EXTENSION     >   CREATE EXTENSION IF NOT EXISTS btree_gist WITH SCHEMA public;
    DROP EXTENSION btree_gist;
                   false            -           0    0    EXTENSION btree_gist    COMMENT     T   COMMENT ON EXTENSION btree_gist IS 'support for indexing common datatypes in GiST';
                        false    3                        3079    18657    postgis 	   EXTENSION     ;   CREATE EXTENSION IF NOT EXISTS postgis WITH SCHEMA public;
    DROP EXTENSION postgis;
                   false            .           0    0    EXTENSION postgis    COMMENT     ^   COMMENT ON EXTENSION postgis IS 'PostGIS geometry and geography spatial types and functions';
                        false    2            �	           1247    30147    accessibilite_pmr_enum    TYPE     �   CREATE TYPE public.accessibilite_pmr_enum AS ENUM (
    'Réservé PMR',
    'Accessible mais non réservé PMR',
    'Non accessible',
    'Accessibilité inconnue'
);
 )   DROP TYPE public.accessibilite_pmr_enum;
       public          qualicharge    false            �	           1247    30123    condition_acces_enum    TYPE     `   CREATE TYPE public.condition_acces_enum AS ENUM (
    'Accès libre',
    'Accès réservé'
);
 '   DROP TYPE public.condition_acces_enum;
       public          qualicharge    false            �	           1247    30163    etat_pdc_enum    TYPE     b   CREATE TYPE public.etat_pdc_enum AS ENUM (
    'en_service',
    'hors_service',
    'inconnu'
);
     DROP TYPE public.etat_pdc_enum;
       public          qualicharge    false            �	           1247    30192    etat_prise_enum    TYPE     e   CREATE TYPE public.etat_prise_enum AS ENUM (
    'fonctionnel',
    'hors_service',
    'inconnu'
);
 "   DROP TYPE public.etat_prise_enum;
       public          qualicharge    false            �	           1247    30105    implantation_station_enum    TYPE     �   CREATE TYPE public.implantation_station_enum AS ENUM (
    'Voirie',
    'Parking public',
    'Parking privé à usage public',
    'Parking privé réservé à la clientèle',
    'Station dédiée à la recharge rapide'
);
 ,   DROP TYPE public.implantation_station_enum;
       public          qualicharge    false            �	           1247    30176    occupation_pdc_enum    TYPE     l   CREATE TYPE public.occupation_pdc_enum AS ENUM (
    'libre',
    'occupe',
    'reserve',
    'inconnu'
);
 &   DROP TYPE public.occupation_pdc_enum;
       public          qualicharge    false            e	           1247    20589    operationalunittypeenum    TYPE     W   CREATE TYPE public.operationalunittypeenum AS ENUM (
    'CHARGING',
    'MOBILITY'
);
 *   DROP TYPE public.operationalunittypeenum;
       public          qualicharge    false            �	           1247    30135    raccordement_enum    TYPE     O   CREATE TYPE public.raccordement_enum AS ENUM (
    'Direct',
    'Indirect'
);
 $   DROP TYPE public.raccordement_enum;
       public          qualicharge    false            $           1255    30352    audit_table(regclass)    FUNCTION     �   CREATE FUNCTION public.audit_table(target_table regclass) RETURNS void
    LANGUAGE sql
    AS $$
SELECT audit_table(target_table, ARRAY[]::text[]);
$$;
 9   DROP FUNCTION public.audit_table(target_table regclass);
       public          qualicharge    false            #           1255    30351    audit_table(regclass, text[])    FUNCTION     "  CREATE FUNCTION public.audit_table(target_table regclass, ignored_cols text[]) RETURNS void
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
       public          qualicharge    false            "           1255    30350    create_activity()    FUNCTION     #  CREATE FUNCTION public.create_activity() RETURNS trigger
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
       public          qualicharge    false            &           1255    30355    get_setting(text, text)    FUNCTION     �   CREATE FUNCTION public.get_setting(setting text, default_value text) RETURNS text
    LANGUAGE sql
    AS $$
    SELECT coalesce(
        nullif(current_setting(setting, 't'), ''),
        default_value
    );
$$;
 D   DROP FUNCTION public.get_setting(setting text, default_value text);
       public          qualicharge    false            !           1255    30349 (   jsonb_change_key_name(jsonb, text, text)    FUNCTION     E  CREATE FUNCTION public.jsonb_change_key_name(data jsonb, old_key text, new_key text) RETURNS jsonb
    LANGUAGE sql IMMUTABLE
    AS $$
    SELECT ('{'||string_agg(to_json(CASE WHEN key = old_key THEN new_key ELSE key END)||':'||value, ',')||'}')::jsonb
    FROM (
        SELECT *
        FROM jsonb_each(data)
    ) t;
$$;
 T   DROP FUNCTION public.jsonb_change_key_name(data jsonb, old_key text, new_key text);
       public          qualicharge    false            %           1255    30353    jsonb_subtract(jsonb, jsonb)    FUNCTION     �   CREATE FUNCTION public.jsonb_subtract(arg1 jsonb, arg2 jsonb) RETURNS jsonb
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
       public          qualicharge    false            R           2617    30354    -    OPERATOR     n   CREATE OPERATOR public.- (
    FUNCTION = public.jsonb_subtract,
    LEFTARG = jsonb,
    RIGHTARG = jsonb
);
 '   DROP OPERATOR public.- (jsonb, jsonb);
       public          qualicharge    false    1573            $           1259    20577    status    TABLE     \  CREATE TABLE public.status (
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
       public         heap    qualicharge    false    2447    2450    2453    2453    2453    2453            =           1259    32420    _hyper_1_10_chunk    TABLE       CREATE TABLE _timescaledb_internal._hyper_1_10_chunk (
    CONSTRAINT constraint_10 CHECK (((horodatage >= '2025-01-09 00:00:00+00'::timestamp with time zone) AND (horodatage < '2025-01-16 00:00:00+00'::timestamp with time zone)))
)
INHERITS (public.status);
 4   DROP TABLE _timescaledb_internal._hyper_1_10_chunk;
       _timescaledb_internal         heap    qualicharge    false    2453    2450    292    4    2453    2453    2453    2447            >           1259    32432    _hyper_1_11_chunk    TABLE       CREATE TABLE _timescaledb_internal._hyper_1_11_chunk (
    CONSTRAINT constraint_11 CHECK (((horodatage >= '2024-12-12 00:00:00+00'::timestamp with time zone) AND (horodatage < '2024-12-19 00:00:00+00'::timestamp with time zone)))
)
INHERITS (public.status);
 4   DROP TABLE _timescaledb_internal._hyper_1_11_chunk;
       _timescaledb_internal         heap    qualicharge    false    292    2450    2453    2453    2447    2453    4    2453            ?           1259    32444    _hyper_1_12_chunk    TABLE       CREATE TABLE _timescaledb_internal._hyper_1_12_chunk (
    CONSTRAINT constraint_12 CHECK (((horodatage >= '2024-12-26 00:00:00+00'::timestamp with time zone) AND (horodatage < '2025-01-02 00:00:00+00'::timestamp with time zone)))
)
INHERITS (public.status);
 4   DROP TABLE _timescaledb_internal._hyper_1_12_chunk;
       _timescaledb_internal         heap    qualicharge    false    2450    2453    2453    2447    2453    2453    4    292            @           1259    32456    _hyper_1_13_chunk    TABLE       CREATE TABLE _timescaledb_internal._hyper_1_13_chunk (
    CONSTRAINT constraint_13 CHECK (((horodatage >= '2024-11-28 00:00:00+00'::timestamp with time zone) AND (horodatage < '2024-12-05 00:00:00+00'::timestamp with time zone)))
)
INHERITS (public.status);
 4   DROP TABLE _timescaledb_internal._hyper_1_13_chunk;
       _timescaledb_internal         heap    qualicharge    false    2453    292    4    2453    2453    2453    2450    2447            A           1259    32468    _hyper_1_14_chunk    TABLE       CREATE TABLE _timescaledb_internal._hyper_1_14_chunk (
    CONSTRAINT constraint_14 CHECK (((horodatage >= '2024-12-05 00:00:00+00'::timestamp with time zone) AND (horodatage < '2024-12-12 00:00:00+00'::timestamp with time zone)))
)
INHERITS (public.status);
 4   DROP TABLE _timescaledb_internal._hyper_1_14_chunk;
       _timescaledb_internal         heap    qualicharge    false    2453    2450    2453    2453    2453    292    4    2447            B           1259    32480    _hyper_1_15_chunk    TABLE       CREATE TABLE _timescaledb_internal._hyper_1_15_chunk (
    CONSTRAINT constraint_15 CHECK (((horodatage >= '2024-07-18 00:00:00+00'::timestamp with time zone) AND (horodatage < '2024-07-25 00:00:00+00'::timestamp with time zone)))
)
INHERITS (public.status);
 4   DROP TABLE _timescaledb_internal._hyper_1_15_chunk;
       _timescaledb_internal         heap    qualicharge    false    2453    292    4    2453    2453    2453    2450    2447            C           1259    32492    _hyper_1_16_chunk    TABLE       CREATE TABLE _timescaledb_internal._hyper_1_16_chunk (
    CONSTRAINT constraint_16 CHECK (((horodatage >= '2024-08-08 00:00:00+00'::timestamp with time zone) AND (horodatage < '2024-08-15 00:00:00+00'::timestamp with time zone)))
)
INHERITS (public.status);
 4   DROP TABLE _timescaledb_internal._hyper_1_16_chunk;
       _timescaledb_internal         heap    qualicharge    false    2450    292    4    2453    2453    2453    2453    2447            D           1259    32511    _hyper_1_17_chunk    TABLE       CREATE TABLE _timescaledb_internal._hyper_1_17_chunk (
    CONSTRAINT constraint_17 CHECK (((horodatage >= '2024-11-14 00:00:00+00'::timestamp with time zone) AND (horodatage < '2024-11-21 00:00:00+00'::timestamp with time zone)))
)
INHERITS (public.status);
 4   DROP TABLE _timescaledb_internal._hyper_1_17_chunk;
       _timescaledb_internal         heap    qualicharge    false    2447    292    4    2453    2453    2453    2450    2453            E           1259    32523    _hyper_1_18_chunk    TABLE       CREATE TABLE _timescaledb_internal._hyper_1_18_chunk (
    CONSTRAINT constraint_18 CHECK (((horodatage >= '2024-08-01 00:00:00+00'::timestamp with time zone) AND (horodatage < '2024-08-08 00:00:00+00'::timestamp with time zone)))
)
INHERITS (public.status);
 4   DROP TABLE _timescaledb_internal._hyper_1_18_chunk;
       _timescaledb_internal         heap    qualicharge    false    2447    4    2453    2453    2453    2453    2450    292            F           1259    32535    _hyper_1_19_chunk    TABLE       CREATE TABLE _timescaledb_internal._hyper_1_19_chunk (
    CONSTRAINT constraint_19 CHECK (((horodatage >= '2024-08-22 00:00:00+00'::timestamp with time zone) AND (horodatage < '2024-08-29 00:00:00+00'::timestamp with time zone)))
)
INHERITS (public.status);
 4   DROP TABLE _timescaledb_internal._hyper_1_19_chunk;
       _timescaledb_internal         heap    qualicharge    false    2450    2447    4    2453    2453    2453    2453    292            G           1259    32547    _hyper_1_20_chunk    TABLE       CREATE TABLE _timescaledb_internal._hyper_1_20_chunk (
    CONSTRAINT constraint_20 CHECK (((horodatage >= '2024-09-12 00:00:00+00'::timestamp with time zone) AND (horodatage < '2024-09-19 00:00:00+00'::timestamp with time zone)))
)
INHERITS (public.status);
 4   DROP TABLE _timescaledb_internal._hyper_1_20_chunk;
       _timescaledb_internal         heap    qualicharge    false    2453    2453    2453    4    292    2453    2450    2447            H           1259    32559    _hyper_1_21_chunk    TABLE       CREATE TABLE _timescaledb_internal._hyper_1_21_chunk (
    CONSTRAINT constraint_21 CHECK (((horodatage >= '2024-07-11 00:00:00+00'::timestamp with time zone) AND (horodatage < '2024-07-18 00:00:00+00'::timestamp with time zone)))
)
INHERITS (public.status);
 4   DROP TABLE _timescaledb_internal._hyper_1_21_chunk;
       _timescaledb_internal         heap    qualicharge    false    4    292    2450    2447    2453    2453    2453    2453            I           1259    32593    _hyper_1_22_chunk    TABLE       CREATE TABLE _timescaledb_internal._hyper_1_22_chunk (
    CONSTRAINT constraint_22 CHECK (((horodatage >= '2024-06-06 00:00:00+00'::timestamp with time zone) AND (horodatage < '2024-06-13 00:00:00+00'::timestamp with time zone)))
)
INHERITS (public.status);
 4   DROP TABLE _timescaledb_internal._hyper_1_22_chunk;
       _timescaledb_internal         heap    qualicharge    false    2450    2453    2453    2447    292    4    2453    2453            J           1259    32648    _hyper_1_23_chunk    TABLE       CREATE TABLE _timescaledb_internal._hyper_1_23_chunk (
    CONSTRAINT constraint_23 CHECK (((horodatage >= '2024-11-21 00:00:00+00'::timestamp with time zone) AND (horodatage < '2024-11-28 00:00:00+00'::timestamp with time zone)))
)
INHERITS (public.status);
 4   DROP TABLE _timescaledb_internal._hyper_1_23_chunk;
       _timescaledb_internal         heap    qualicharge    false    2453    292    4    2453    2453    2453    2450    2447            ;           1259    32396    _hyper_1_8_chunk    TABLE       CREATE TABLE _timescaledb_internal._hyper_1_8_chunk (
    CONSTRAINT constraint_8 CHECK (((horodatage >= '2024-12-19 00:00:00+00'::timestamp with time zone) AND (horodatage < '2024-12-26 00:00:00+00'::timestamp with time zone)))
)
INHERITS (public.status);
 3   DROP TABLE _timescaledb_internal._hyper_1_8_chunk;
       _timescaledb_internal         heap    qualicharge    false    2453    2447    2450    2453    2453    2453    4    292            <           1259    32408    _hyper_1_9_chunk    TABLE       CREATE TABLE _timescaledb_internal._hyper_1_9_chunk (
    CONSTRAINT constraint_9 CHECK (((horodatage >= '2025-01-02 00:00:00+00'::timestamp with time zone) AND (horodatage < '2025-01-09 00:00:00+00'::timestamp with time zone)))
)
INHERITS (public.status);
 3   DROP TABLE _timescaledb_internal._hyper_1_9_chunk;
       _timescaledb_internal         heap    qualicharge    false    2453    2450    292    2453    2453    4    2447    2453            #           1259    20541    session    TABLE     �  CREATE TABLE public.session (
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
       public         heap    qualicharge    false            4           1259    32218    _hyper_2_1_chunk    TABLE     �   CREATE TABLE _timescaledb_internal._hyper_2_1_chunk (
    CONSTRAINT constraint_1 CHECK (((start >= '2024-12-05 00:00:00+00'::timestamp with time zone) AND (start < '2024-12-12 00:00:00+00'::timestamp with time zone)))
)
INHERITS (public.session);
 3   DROP TABLE _timescaledb_internal._hyper_2_1_chunk;
       _timescaledb_internal         heap    qualicharge    false    291    4            5           1259    32240    _hyper_2_2_chunk    TABLE     �   CREATE TABLE _timescaledb_internal._hyper_2_2_chunk (
    CONSTRAINT constraint_2 CHECK (((start >= '2024-12-26 00:00:00+00'::timestamp with time zone) AND (start < '2025-01-02 00:00:00+00'::timestamp with time zone)))
)
INHERITS (public.session);
 3   DROP TABLE _timescaledb_internal._hyper_2_2_chunk;
       _timescaledb_internal         heap    qualicharge    false    291    4            6           1259    32262    _hyper_2_3_chunk    TABLE     �   CREATE TABLE _timescaledb_internal._hyper_2_3_chunk (
    CONSTRAINT constraint_3 CHECK (((start >= '2024-12-19 00:00:00+00'::timestamp with time zone) AND (start < '2024-12-26 00:00:00+00'::timestamp with time zone)))
)
INHERITS (public.session);
 3   DROP TABLE _timescaledb_internal._hyper_2_3_chunk;
       _timescaledb_internal         heap    qualicharge    false    291    4            7           1259    32284    _hyper_2_4_chunk    TABLE     �   CREATE TABLE _timescaledb_internal._hyper_2_4_chunk (
    CONSTRAINT constraint_4 CHECK (((start >= '2024-12-12 00:00:00+00'::timestamp with time zone) AND (start < '2024-12-19 00:00:00+00'::timestamp with time zone)))
)
INHERITS (public.session);
 3   DROP TABLE _timescaledb_internal._hyper_2_4_chunk;
       _timescaledb_internal         heap    qualicharge    false    4    291            8           1259    32306    _hyper_2_5_chunk    TABLE     �   CREATE TABLE _timescaledb_internal._hyper_2_5_chunk (
    CONSTRAINT constraint_5 CHECK (((start >= '2025-01-02 00:00:00+00'::timestamp with time zone) AND (start < '2025-01-09 00:00:00+00'::timestamp with time zone)))
)
INHERITS (public.session);
 3   DROP TABLE _timescaledb_internal._hyper_2_5_chunk;
       _timescaledb_internal         heap    qualicharge    false    4    291            9           1259    32328    _hyper_2_6_chunk    TABLE     �   CREATE TABLE _timescaledb_internal._hyper_2_6_chunk (
    CONSTRAINT constraint_6 CHECK (((start >= '2025-01-09 00:00:00+00'::timestamp with time zone) AND (start < '2025-01-16 00:00:00+00'::timestamp with time zone)))
)
INHERITS (public.session);
 3   DROP TABLE _timescaledb_internal._hyper_2_6_chunk;
       _timescaledb_internal         heap    qualicharge    false    291    4            :           1259    32350    _hyper_2_7_chunk    TABLE     �   CREATE TABLE _timescaledb_internal._hyper_2_7_chunk (
    CONSTRAINT constraint_7 CHECK (((start >= '2024-11-28 00:00:00+00'::timestamp with time zone) AND (start < '2024-12-05 00:00:00+00'::timestamp with time zone)))
)
INHERITS (public.session);
 3   DROP TABLE _timescaledb_internal._hyper_2_7_chunk;
       _timescaledb_internal         heap    qualicharge    false    4    291            2           1259    30243    activity    TABLE     B  CREATE TABLE public.activity (
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
       public         heap    qualicharge    false            1           1259    30242    activity_id_seq    SEQUENCE     x   CREATE SEQUENCE public.activity_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;
 &   DROP SEQUENCE public.activity_id_seq;
       public          qualicharge    false    306            /           0    0    activity_id_seq    SEQUENCE OWNED BY     C   ALTER SEQUENCE public.activity_id_seq OWNED BY public.activity.id;
          public          qualicharge    false    305                       1259    20404    alembic_version    TABLE     X   CREATE TABLE public.alembic_version (
    version_num character varying(32) NOT NULL
);
 #   DROP TABLE public.alembic_version;
       public         heap    qualicharge    false                       1259    20409 	   amenageur    TABLE     �  CREATE TABLE public.amenageur (
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
       public         heap    qualicharge    false            *           1259    21490    city    TABLE     t  CREATE TABLE public.city (
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
       public         heap    qualicharge    false    2    2    2    2    2    2    2    2            +           1259    23120 
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
       public         heap    qualicharge    false    2    2    2    2    2    2    2    2                       1259    20419    enseigne    TABLE     A  CREATE TABLE public.enseigne (
    created_at timestamp with time zone NOT NULL,
    updated_at timestamp with time zone NOT NULL,
    id uuid NOT NULL,
    nom_enseigne character varying NOT NULL,
    created_by_id uuid,
    updated_by_id uuid,
    CONSTRAINT "pre-creation-update" CHECK ((created_at <= updated_at))
);
    DROP TABLE public.enseigne;
       public         heap    qualicharge    false            ,           1259    23437    epci    TABLE     J  CREATE TABLE public.epci (
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
       public         heap    qualicharge    false    2    2    2    2    2    2    2    2            &           1259    20607    group    TABLE     8  CREATE TABLE public."group" (
    created_at timestamp with time zone NOT NULL,
    updated_at timestamp with time zone NOT NULL,
    id uuid NOT NULL,
    name character varying NOT NULL,
    created_by_id uuid,
    updated_by_id uuid,
    CONSTRAINT "pre-creation-update" CHECK ((created_at <= updated_at))
);
    DROP TABLE public."group";
       public         heap    qualicharge    false            (           1259    20627    groupoperationalunit    TABLE     p   CREATE TABLE public.groupoperationalunit (
    group_id uuid NOT NULL,
    operational_unit_id uuid NOT NULL
);
 (   DROP TABLE public.groupoperationalunit;
       public         heap    qualicharge    false            3           1259    30398    lateststatus    TABLE     a  CREATE TABLE public.lateststatus (
    horodatage timestamp with time zone NOT NULL,
    etat_pdc public.etat_pdc_enum NOT NULL,
    occupation_pdc public.occupation_pdc_enum NOT NULL,
    etat_prise_type_2 public.etat_prise_enum,
    etat_prise_type_combo_ccs public.etat_prise_enum,
    etat_prise_type_chademo public.etat_prise_enum,
    etat_prise_type_ef public.etat_prise_enum,
    id_pdc_itinerance character varying NOT NULL,
    created_at timestamp with time zone NOT NULL,
    updated_at timestamp with time zone NOT NULL,
    CONSTRAINT "pre-creation-update" CHECK ((created_at <= updated_at))
);
     DROP TABLE public.lateststatus;
       public         heap    qualicharge    false    2453    2453    2453    2450    2447    2453                       1259    20429    localisation    TABLE     �  CREATE TABLE public.localisation (
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
       public         heap    qualicharge    false    2    2    2    2    2    2    2    2                        1259    20440 	   operateur    TABLE     �  CREATE TABLE public.operateur (
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
       public         heap    qualicharge    false            %           1259    20593    operationalunit    TABLE     g  CREATE TABLE public.operationalunit (
    created_at timestamp with time zone NOT NULL,
    updated_at timestamp with time zone NOT NULL,
    id uuid NOT NULL,
    code character varying NOT NULL,
    name character varying NOT NULL,
    type public.operationalunittypeenum NOT NULL,
    CONSTRAINT "pre-creation-update" CHECK ((created_at <= updated_at))
);
 #   DROP TABLE public.operationalunit;
       public         heap    qualicharge    false    2405            "           1259    20511    pointdecharge    TABLE     �  CREATE TABLE public.pointdecharge (
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
       public         heap    qualicharge    false    2444            -           1259    25269    region    TABLE     L  CREATE TABLE public.region (
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
       public         heap    qualicharge    false    2    2    2    2    2    2    2    2            !           1259    20473    station    TABLE     �  CREATE TABLE public.station (
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
       public         heap    qualicharge    false    2435    2441    2438            .           1259    30221    statique    MATERIALIZED VIEW     7  CREATE MATERIALIZED VIEW public.statique AS
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
       public         heap    qualicharge    false    289    285    285    286    286    287    287    287    287    288    288    288    288    289    289    289    289    289    285    289    289    289    289    289    289    289    289    289    289    289    290    290    290    290    290    290    290    290    290    290    290    290    290    290    290    290    290    290    290    290    290    2    2    2    2    2    2    2    2    2    285    2444    2435    2441    2438            0           1259    30232    transaction    TABLE     �   CREATE TABLE public.transaction (
    id bigint NOT NULL,
    native_transaction_id bigint,
    issued_at timestamp without time zone,
    client_addr inet,
    actor_id text
);
    DROP TABLE public.transaction;
       public         heap    qualicharge    false            /           1259    30231    transaction_id_seq    SEQUENCE     {   CREATE SEQUENCE public.transaction_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;
 )   DROP SEQUENCE public.transaction_id_seq;
       public          qualicharge    false    304            0           0    0    transaction_id_seq    SEQUENCE OWNED BY     I   ALTER SEQUENCE public.transaction_id_seq OWNED BY public.transaction.id;
          public          qualicharge    false    303            '           1259    20617    user    TABLE     �  CREATE TABLE public."user" (
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
       public         heap    qualicharge    false            )           1259    20642 	   usergroup    TABLE     Y   CREATE TABLE public.usergroup (
    user_id uuid NOT NULL,
    group_id uuid NOT NULL
);
    DROP TABLE public.usergroup;
       public         heap    qualicharge    false                       2604    30246    activity id    DEFAULT     j   ALTER TABLE ONLY public.activity ALTER COLUMN id SET DEFAULT nextval('public.activity_id_seq'::regclass);
 :   ALTER TABLE public.activity ALTER COLUMN id DROP DEFAULT;
       public          qualicharge    false    305    306    306                       2604    30235    transaction id    DEFAULT     p   ALTER TABLE ONLY public.transaction ALTER COLUMN id SET DEFAULT nextval('public.transaction_id_seq'::regclass);
 =   ALTER TABLE public.transaction ALTER COLUMN id DROP DEFAULT;
       public          qualicharge    false    303    304    304            �           2606    30252    activity activity_pkey 
   CONSTRAINT     T   ALTER TABLE ONLY public.activity
    ADD CONSTRAINT activity_pkey PRIMARY KEY (id);
 @   ALTER TABLE ONLY public.activity DROP CONSTRAINT activity_pkey;
       public            qualicharge    false    306            �           2606    20408 #   alembic_version alembic_version_pkc 
   CONSTRAINT     j   ALTER TABLE ONLY public.alembic_version
    ADD CONSTRAINT alembic_version_pkc PRIMARY KEY (version_num);
 M   ALTER TABLE ONLY public.alembic_version DROP CONSTRAINT alembic_version_pkc;
       public            qualicharge    false    284            �           2606    20418 G   amenageur amenageur_nom_amenageur_siren_amenageur_contact_amenageur_key 
   CONSTRAINT     �   ALTER TABLE ONLY public.amenageur
    ADD CONSTRAINT amenageur_nom_amenageur_siren_amenageur_contact_amenageur_key UNIQUE (nom_amenageur, siren_amenageur, contact_amenageur);
 q   ALTER TABLE ONLY public.amenageur DROP CONSTRAINT amenageur_nom_amenageur_siren_amenageur_contact_amenageur_key;
       public            qualicharge    false    285    285    285            �           2606    20416    amenageur amenageur_pkey 
   CONSTRAINT     V   ALTER TABLE ONLY public.amenageur
    ADD CONSTRAINT amenageur_pkey PRIMARY KEY (id);
 B   ALTER TABLE ONLY public.amenageur DROP CONSTRAINT amenageur_pkey;
       public            qualicharge    false    285            �           2606    29983    city city_pkey 
   CONSTRAINT     L   ALTER TABLE ONLY public.city
    ADD CONSTRAINT city_pkey PRIMARY KEY (id);
 8   ALTER TABLE ONLY public.city DROP CONSTRAINT city_pkey;
       public            qualicharge    false    298            �           2606    29979    department department_pkey 
   CONSTRAINT     X   ALTER TABLE ONLY public.department
    ADD CONSTRAINT department_pkey PRIMARY KEY (id);
 D   ALTER TABLE ONLY public.department DROP CONSTRAINT department_pkey;
       public            qualicharge    false    299            �           2606    20428 "   enseigne enseigne_nom_enseigne_key 
   CONSTRAINT     e   ALTER TABLE ONLY public.enseigne
    ADD CONSTRAINT enseigne_nom_enseigne_key UNIQUE (nom_enseigne);
 L   ALTER TABLE ONLY public.enseigne DROP CONSTRAINT enseigne_nom_enseigne_key;
       public            qualicharge    false    286            �           2606    20426    enseigne enseigne_pkey 
   CONSTRAINT     T   ALTER TABLE ONLY public.enseigne
    ADD CONSTRAINT enseigne_pkey PRIMARY KEY (id);
 @   ALTER TABLE ONLY public.enseigne DROP CONSTRAINT enseigne_pkey;
       public            qualicharge    false    286            �           2606    29981    epci epci_pkey 
   CONSTRAINT     L   ALTER TABLE ONLY public.epci
    ADD CONSTRAINT epci_pkey PRIMARY KEY (id);
 8   ALTER TABLE ONLY public.epci DROP CONSTRAINT epci_pkey;
       public            qualicharge    false    300            �           2606    20616    group group_name_key 
   CONSTRAINT     Q   ALTER TABLE ONLY public."group"
    ADD CONSTRAINT group_name_key UNIQUE (name);
 @   ALTER TABLE ONLY public."group" DROP CONSTRAINT group_name_key;
       public            qualicharge    false    294            �           2606    20614    group group_pkey 
   CONSTRAINT     P   ALTER TABLE ONLY public."group"
    ADD CONSTRAINT group_pkey PRIMARY KEY (id);
 <   ALTER TABLE ONLY public."group" DROP CONSTRAINT group_pkey;
       public            qualicharge    false    294            �           2606    20631 .   groupoperationalunit groupoperationalunit_pkey 
   CONSTRAINT     �   ALTER TABLE ONLY public.groupoperationalunit
    ADD CONSTRAINT groupoperationalunit_pkey PRIMARY KEY (group_id, operational_unit_id);
 X   ALTER TABLE ONLY public.groupoperationalunit DROP CONSTRAINT groupoperationalunit_pkey;
       public            qualicharge    false    296    296            �           2606    30405    lateststatus lateststatus_pkey 
   CONSTRAINT     k   ALTER TABLE ONLY public.lateststatus
    ADD CONSTRAINT lateststatus_pkey PRIMARY KEY (id_pdc_itinerance);
 H   ALTER TABLE ONLY public.lateststatus DROP CONSTRAINT lateststatus_pkey;
       public            qualicharge    false    307            �           2606    30037 +   localisation localisation_coordonneesXY_key 
   CONSTRAINT     s   ALTER TABLE ONLY public.localisation
    ADD CONSTRAINT "localisation_coordonneesXY_key" UNIQUE ("coordonneesXY");
 W   ALTER TABLE ONLY public.localisation DROP CONSTRAINT "localisation_coordonneesXY_key";
       public            qualicharge    false    287            �           2606    20436    localisation localisation_pkey 
   CONSTRAINT     \   ALTER TABLE ONLY public.localisation
    ADD CONSTRAINT localisation_pkey PRIMARY KEY (id);
 H   ALTER TABLE ONLY public.localisation DROP CONSTRAINT localisation_pkey;
       public            qualicharge    false    287            �           2606    20449 I   operateur operateur_nom_operateur_contact_operateur_telephone_operate_key 
   CONSTRAINT     �   ALTER TABLE ONLY public.operateur
    ADD CONSTRAINT operateur_nom_operateur_contact_operateur_telephone_operate_key UNIQUE (nom_operateur, contact_operateur, telephone_operateur);
 s   ALTER TABLE ONLY public.operateur DROP CONSTRAINT operateur_nom_operateur_contact_operateur_telephone_operate_key;
       public            qualicharge    false    288    288    288            �           2606    20447    operateur operateur_pkey 
   CONSTRAINT     V   ALTER TABLE ONLY public.operateur
    ADD CONSTRAINT operateur_pkey PRIMARY KEY (id);
 B   ALTER TABLE ONLY public.operateur DROP CONSTRAINT operateur_pkey;
       public            qualicharge    false    288            �           2606    20600 $   operationalunit operationalunit_pkey 
   CONSTRAINT     b   ALTER TABLE ONLY public.operationalunit
    ADD CONSTRAINT operationalunit_pkey PRIMARY KEY (id);
 N   ALTER TABLE ONLY public.operationalunit DROP CONSTRAINT operationalunit_pkey;
       public            qualicharge    false    293            �           2606    20518     pointdecharge pointdecharge_pkey 
   CONSTRAINT     ^   ALTER TABLE ONLY public.pointdecharge
    ADD CONSTRAINT pointdecharge_pkey PRIMARY KEY (id);
 J   ALTER TABLE ONLY public.pointdecharge DROP CONSTRAINT pointdecharge_pkey;
       public            qualicharge    false    290            �           2606    29977    region region_pkey 
   CONSTRAINT     P   ALTER TABLE ONLY public.region
    ADD CONSTRAINT region_pkey PRIMARY KEY (id);
 <   ALTER TABLE ONLY public.region DROP CONSTRAINT region_pkey;
       public            qualicharge    false    301            �           2606    20480    station station_pkey 
   CONSTRAINT     R   ALTER TABLE ONLY public.station
    ADD CONSTRAINT station_pkey PRIMARY KEY (id);
 >   ALTER TABLE ONLY public.station DROP CONSTRAINT station_pkey;
       public            qualicharge    false    289            �           2606    30239    transaction transaction_pkey 
   CONSTRAINT     Z   ALTER TABLE ONLY public.transaction
    ADD CONSTRAINT transaction_pkey PRIMARY KEY (id);
 F   ALTER TABLE ONLY public.transaction DROP CONSTRAINT transaction_pkey;
       public            qualicharge    false    304            �           2606    30241 +   transaction transaction_unique_native_tx_id 
   CONSTRAINT     �   ALTER TABLE ONLY public.transaction
    ADD CONSTRAINT transaction_unique_native_tx_id EXCLUDE USING gist (native_transaction_id WITH =, tsrange((issued_at - '01:00:00'::interval), issued_at) WITH &&);
 U   ALTER TABLE ONLY public.transaction DROP CONSTRAINT transaction_unique_native_tx_id;
       public            qualicharge    false    304            �           2606    20658    user user_email_key 
   CONSTRAINT     Q   ALTER TABLE ONLY public."user"
    ADD CONSTRAINT user_email_key UNIQUE (email);
 ?   ALTER TABLE ONLY public."user" DROP CONSTRAINT user_email_key;
       public            qualicharge    false    295            �           2606    20624    user user_pkey 
   CONSTRAINT     N   ALTER TABLE ONLY public."user"
    ADD CONSTRAINT user_pkey PRIMARY KEY (id);
 :   ALTER TABLE ONLY public."user" DROP CONSTRAINT user_pkey;
       public            qualicharge    false    295            �           2606    20626    user user_username_key 
   CONSTRAINT     W   ALTER TABLE ONLY public."user"
    ADD CONSTRAINT user_username_key UNIQUE (username);
 B   ALTER TABLE ONLY public."user" DROP CONSTRAINT user_username_key;
       public            qualicharge    false    295            �           2606    20646    usergroup usergroup_pkey 
   CONSTRAINT     e   ALTER TABLE ONLY public.usergroup
    ADD CONSTRAINT usergroup_pkey PRIMARY KEY (user_id, group_id);
 B   ALTER TABLE ONLY public.usergroup DROP CONSTRAINT usergroup_pkey;
       public            qualicharge    false    297    297                       1259    32431 )   _hyper_1_10_chunk_ix_status_id_horodatage    INDEX     �   CREATE UNIQUE INDEX _hyper_1_10_chunk_ix_status_id_horodatage ON _timescaledb_internal._hyper_1_10_chunk USING btree (id, horodatage);
 L   DROP INDEX _timescaledb_internal._hyper_1_10_chunk_ix_status_id_horodatage;
       _timescaledb_internal            qualicharge    false    317    317                       1259    32430 "   _hyper_1_10_chunk_ix_status_pdc_id    INDEX     }   CREATE INDEX _hyper_1_10_chunk_ix_status_pdc_id ON _timescaledb_internal._hyper_1_10_chunk USING btree (point_de_charge_id);
 E   DROP INDEX _timescaledb_internal._hyper_1_10_chunk_ix_status_pdc_id;
       _timescaledb_internal            qualicharge    false    317                       1259    32443 )   _hyper_1_11_chunk_ix_status_id_horodatage    INDEX     �   CREATE UNIQUE INDEX _hyper_1_11_chunk_ix_status_id_horodatage ON _timescaledb_internal._hyper_1_11_chunk USING btree (id, horodatage);
 L   DROP INDEX _timescaledb_internal._hyper_1_11_chunk_ix_status_id_horodatage;
       _timescaledb_internal            qualicharge    false    318    318                       1259    32442 "   _hyper_1_11_chunk_ix_status_pdc_id    INDEX     }   CREATE INDEX _hyper_1_11_chunk_ix_status_pdc_id ON _timescaledb_internal._hyper_1_11_chunk USING btree (point_de_charge_id);
 E   DROP INDEX _timescaledb_internal._hyper_1_11_chunk_ix_status_pdc_id;
       _timescaledb_internal            qualicharge    false    318                       1259    32455 )   _hyper_1_12_chunk_ix_status_id_horodatage    INDEX     �   CREATE UNIQUE INDEX _hyper_1_12_chunk_ix_status_id_horodatage ON _timescaledb_internal._hyper_1_12_chunk USING btree (id, horodatage);
 L   DROP INDEX _timescaledb_internal._hyper_1_12_chunk_ix_status_id_horodatage;
       _timescaledb_internal            qualicharge    false    319    319                       1259    32454 "   _hyper_1_12_chunk_ix_status_pdc_id    INDEX     }   CREATE INDEX _hyper_1_12_chunk_ix_status_pdc_id ON _timescaledb_internal._hyper_1_12_chunk USING btree (point_de_charge_id);
 E   DROP INDEX _timescaledb_internal._hyper_1_12_chunk_ix_status_pdc_id;
       _timescaledb_internal            qualicharge    false    319                       1259    32467 )   _hyper_1_13_chunk_ix_status_id_horodatage    INDEX     �   CREATE UNIQUE INDEX _hyper_1_13_chunk_ix_status_id_horodatage ON _timescaledb_internal._hyper_1_13_chunk USING btree (id, horodatage);
 L   DROP INDEX _timescaledb_internal._hyper_1_13_chunk_ix_status_id_horodatage;
       _timescaledb_internal            qualicharge    false    320    320            	           1259    32466 "   _hyper_1_13_chunk_ix_status_pdc_id    INDEX     }   CREATE INDEX _hyper_1_13_chunk_ix_status_pdc_id ON _timescaledb_internal._hyper_1_13_chunk USING btree (point_de_charge_id);
 E   DROP INDEX _timescaledb_internal._hyper_1_13_chunk_ix_status_pdc_id;
       _timescaledb_internal            qualicharge    false    320            
           1259    32479 )   _hyper_1_14_chunk_ix_status_id_horodatage    INDEX     �   CREATE UNIQUE INDEX _hyper_1_14_chunk_ix_status_id_horodatage ON _timescaledb_internal._hyper_1_14_chunk USING btree (id, horodatage);
 L   DROP INDEX _timescaledb_internal._hyper_1_14_chunk_ix_status_id_horodatage;
       _timescaledb_internal            qualicharge    false    321    321                       1259    32478 "   _hyper_1_14_chunk_ix_status_pdc_id    INDEX     }   CREATE INDEX _hyper_1_14_chunk_ix_status_pdc_id ON _timescaledb_internal._hyper_1_14_chunk USING btree (point_de_charge_id);
 E   DROP INDEX _timescaledb_internal._hyper_1_14_chunk_ix_status_pdc_id;
       _timescaledb_internal            qualicharge    false    321                       1259    32491 )   _hyper_1_15_chunk_ix_status_id_horodatage    INDEX     �   CREATE UNIQUE INDEX _hyper_1_15_chunk_ix_status_id_horodatage ON _timescaledb_internal._hyper_1_15_chunk USING btree (id, horodatage);
 L   DROP INDEX _timescaledb_internal._hyper_1_15_chunk_ix_status_id_horodatage;
       _timescaledb_internal            qualicharge    false    322    322                       1259    32490 "   _hyper_1_15_chunk_ix_status_pdc_id    INDEX     }   CREATE INDEX _hyper_1_15_chunk_ix_status_pdc_id ON _timescaledb_internal._hyper_1_15_chunk USING btree (point_de_charge_id);
 E   DROP INDEX _timescaledb_internal._hyper_1_15_chunk_ix_status_pdc_id;
       _timescaledb_internal            qualicharge    false    322                       1259    32503 )   _hyper_1_16_chunk_ix_status_id_horodatage    INDEX     �   CREATE UNIQUE INDEX _hyper_1_16_chunk_ix_status_id_horodatage ON _timescaledb_internal._hyper_1_16_chunk USING btree (id, horodatage);
 L   DROP INDEX _timescaledb_internal._hyper_1_16_chunk_ix_status_id_horodatage;
       _timescaledb_internal            qualicharge    false    323    323                       1259    32502 "   _hyper_1_16_chunk_ix_status_pdc_id    INDEX     }   CREATE INDEX _hyper_1_16_chunk_ix_status_pdc_id ON _timescaledb_internal._hyper_1_16_chunk USING btree (point_de_charge_id);
 E   DROP INDEX _timescaledb_internal._hyper_1_16_chunk_ix_status_pdc_id;
       _timescaledb_internal            qualicharge    false    323                       1259    32522 )   _hyper_1_17_chunk_ix_status_id_horodatage    INDEX     �   CREATE UNIQUE INDEX _hyper_1_17_chunk_ix_status_id_horodatage ON _timescaledb_internal._hyper_1_17_chunk USING btree (id, horodatage);
 L   DROP INDEX _timescaledb_internal._hyper_1_17_chunk_ix_status_id_horodatage;
       _timescaledb_internal            qualicharge    false    324    324                       1259    32521 "   _hyper_1_17_chunk_ix_status_pdc_id    INDEX     }   CREATE INDEX _hyper_1_17_chunk_ix_status_pdc_id ON _timescaledb_internal._hyper_1_17_chunk USING btree (point_de_charge_id);
 E   DROP INDEX _timescaledb_internal._hyper_1_17_chunk_ix_status_pdc_id;
       _timescaledb_internal            qualicharge    false    324                       1259    32534 )   _hyper_1_18_chunk_ix_status_id_horodatage    INDEX     �   CREATE UNIQUE INDEX _hyper_1_18_chunk_ix_status_id_horodatage ON _timescaledb_internal._hyper_1_18_chunk USING btree (id, horodatage);
 L   DROP INDEX _timescaledb_internal._hyper_1_18_chunk_ix_status_id_horodatage;
       _timescaledb_internal            qualicharge    false    325    325                       1259    32533 "   _hyper_1_18_chunk_ix_status_pdc_id    INDEX     }   CREATE INDEX _hyper_1_18_chunk_ix_status_pdc_id ON _timescaledb_internal._hyper_1_18_chunk USING btree (point_de_charge_id);
 E   DROP INDEX _timescaledb_internal._hyper_1_18_chunk_ix_status_pdc_id;
       _timescaledb_internal            qualicharge    false    325                       1259    32546 )   _hyper_1_19_chunk_ix_status_id_horodatage    INDEX     �   CREATE UNIQUE INDEX _hyper_1_19_chunk_ix_status_id_horodatage ON _timescaledb_internal._hyper_1_19_chunk USING btree (id, horodatage);
 L   DROP INDEX _timescaledb_internal._hyper_1_19_chunk_ix_status_id_horodatage;
       _timescaledb_internal            qualicharge    false    326    326                       1259    32545 "   _hyper_1_19_chunk_ix_status_pdc_id    INDEX     }   CREATE INDEX _hyper_1_19_chunk_ix_status_pdc_id ON _timescaledb_internal._hyper_1_19_chunk USING btree (point_de_charge_id);
 E   DROP INDEX _timescaledb_internal._hyper_1_19_chunk_ix_status_pdc_id;
       _timescaledb_internal            qualicharge    false    326                       1259    32558 )   _hyper_1_20_chunk_ix_status_id_horodatage    INDEX     �   CREATE UNIQUE INDEX _hyper_1_20_chunk_ix_status_id_horodatage ON _timescaledb_internal._hyper_1_20_chunk USING btree (id, horodatage);
 L   DROP INDEX _timescaledb_internal._hyper_1_20_chunk_ix_status_id_horodatage;
       _timescaledb_internal            qualicharge    false    327    327                       1259    32557 "   _hyper_1_20_chunk_ix_status_pdc_id    INDEX     }   CREATE INDEX _hyper_1_20_chunk_ix_status_pdc_id ON _timescaledb_internal._hyper_1_20_chunk USING btree (point_de_charge_id);
 E   DROP INDEX _timescaledb_internal._hyper_1_20_chunk_ix_status_pdc_id;
       _timescaledb_internal            qualicharge    false    327                       1259    32570 )   _hyper_1_21_chunk_ix_status_id_horodatage    INDEX     �   CREATE UNIQUE INDEX _hyper_1_21_chunk_ix_status_id_horodatage ON _timescaledb_internal._hyper_1_21_chunk USING btree (id, horodatage);
 L   DROP INDEX _timescaledb_internal._hyper_1_21_chunk_ix_status_id_horodatage;
       _timescaledb_internal            qualicharge    false    328    328                       1259    32569 "   _hyper_1_21_chunk_ix_status_pdc_id    INDEX     }   CREATE INDEX _hyper_1_21_chunk_ix_status_pdc_id ON _timescaledb_internal._hyper_1_21_chunk USING btree (point_de_charge_id);
 E   DROP INDEX _timescaledb_internal._hyper_1_21_chunk_ix_status_pdc_id;
       _timescaledb_internal            qualicharge    false    328                       1259    32604 )   _hyper_1_22_chunk_ix_status_id_horodatage    INDEX     �   CREATE UNIQUE INDEX _hyper_1_22_chunk_ix_status_id_horodatage ON _timescaledb_internal._hyper_1_22_chunk USING btree (id, horodatage);
 L   DROP INDEX _timescaledb_internal._hyper_1_22_chunk_ix_status_id_horodatage;
       _timescaledb_internal            qualicharge    false    329    329                       1259    32603 "   _hyper_1_22_chunk_ix_status_pdc_id    INDEX     }   CREATE INDEX _hyper_1_22_chunk_ix_status_pdc_id ON _timescaledb_internal._hyper_1_22_chunk USING btree (point_de_charge_id);
 E   DROP INDEX _timescaledb_internal._hyper_1_22_chunk_ix_status_pdc_id;
       _timescaledb_internal            qualicharge    false    329                       1259    32659 )   _hyper_1_23_chunk_ix_status_id_horodatage    INDEX     �   CREATE UNIQUE INDEX _hyper_1_23_chunk_ix_status_id_horodatage ON _timescaledb_internal._hyper_1_23_chunk USING btree (id, horodatage);
 L   DROP INDEX _timescaledb_internal._hyper_1_23_chunk_ix_status_id_horodatage;
       _timescaledb_internal            qualicharge    false    330    330                       1259    32658 "   _hyper_1_23_chunk_ix_status_pdc_id    INDEX     }   CREATE INDEX _hyper_1_23_chunk_ix_status_pdc_id ON _timescaledb_internal._hyper_1_23_chunk USING btree (point_de_charge_id);
 E   DROP INDEX _timescaledb_internal._hyper_1_23_chunk_ix_status_pdc_id;
       _timescaledb_internal            qualicharge    false    330            �           1259    32407 (   _hyper_1_8_chunk_ix_status_id_horodatage    INDEX     �   CREATE UNIQUE INDEX _hyper_1_8_chunk_ix_status_id_horodatage ON _timescaledb_internal._hyper_1_8_chunk USING btree (id, horodatage);
 K   DROP INDEX _timescaledb_internal._hyper_1_8_chunk_ix_status_id_horodatage;
       _timescaledb_internal            qualicharge    false    315    315            �           1259    32406 !   _hyper_1_8_chunk_ix_status_pdc_id    INDEX     {   CREATE INDEX _hyper_1_8_chunk_ix_status_pdc_id ON _timescaledb_internal._hyper_1_8_chunk USING btree (point_de_charge_id);
 D   DROP INDEX _timescaledb_internal._hyper_1_8_chunk_ix_status_pdc_id;
       _timescaledb_internal            qualicharge    false    315                        1259    32419 (   _hyper_1_9_chunk_ix_status_id_horodatage    INDEX     �   CREATE UNIQUE INDEX _hyper_1_9_chunk_ix_status_id_horodatage ON _timescaledb_internal._hyper_1_9_chunk USING btree (id, horodatage);
 K   DROP INDEX _timescaledb_internal._hyper_1_9_chunk_ix_status_id_horodatage;
       _timescaledb_internal            qualicharge    false    316    316                       1259    32418 !   _hyper_1_9_chunk_ix_status_pdc_id    INDEX     {   CREATE INDEX _hyper_1_9_chunk_ix_status_pdc_id ON _timescaledb_internal._hyper_1_9_chunk USING btree (point_de_charge_id);
 D   DROP INDEX _timescaledb_internal._hyper_1_9_chunk_ix_status_pdc_id;
       _timescaledb_internal            qualicharge    false    316            �           1259    32239 $   _hyper_2_1_chunk_ix_session_id_start    INDEX     |   CREATE UNIQUE INDEX _hyper_2_1_chunk_ix_session_id_start ON _timescaledb_internal._hyper_2_1_chunk USING btree (id, start);
 G   DROP INDEX _timescaledb_internal._hyper_2_1_chunk_ix_session_id_start;
       _timescaledb_internal            qualicharge    false    308    308            �           1259    32238 "   _hyper_2_1_chunk_ix_session_pdc_id    INDEX     |   CREATE INDEX _hyper_2_1_chunk_ix_session_pdc_id ON _timescaledb_internal._hyper_2_1_chunk USING btree (point_de_charge_id);
 E   DROP INDEX _timescaledb_internal._hyper_2_1_chunk_ix_session_pdc_id;
       _timescaledb_internal            qualicharge    false    308            �           1259    32261 $   _hyper_2_2_chunk_ix_session_id_start    INDEX     |   CREATE UNIQUE INDEX _hyper_2_2_chunk_ix_session_id_start ON _timescaledb_internal._hyper_2_2_chunk USING btree (id, start);
 G   DROP INDEX _timescaledb_internal._hyper_2_2_chunk_ix_session_id_start;
       _timescaledb_internal            qualicharge    false    309    309            �           1259    32260 "   _hyper_2_2_chunk_ix_session_pdc_id    INDEX     |   CREATE INDEX _hyper_2_2_chunk_ix_session_pdc_id ON _timescaledb_internal._hyper_2_2_chunk USING btree (point_de_charge_id);
 E   DROP INDEX _timescaledb_internal._hyper_2_2_chunk_ix_session_pdc_id;
       _timescaledb_internal            qualicharge    false    309            �           1259    32283 $   _hyper_2_3_chunk_ix_session_id_start    INDEX     |   CREATE UNIQUE INDEX _hyper_2_3_chunk_ix_session_id_start ON _timescaledb_internal._hyper_2_3_chunk USING btree (id, start);
 G   DROP INDEX _timescaledb_internal._hyper_2_3_chunk_ix_session_id_start;
       _timescaledb_internal            qualicharge    false    310    310            �           1259    32282 "   _hyper_2_3_chunk_ix_session_pdc_id    INDEX     |   CREATE INDEX _hyper_2_3_chunk_ix_session_pdc_id ON _timescaledb_internal._hyper_2_3_chunk USING btree (point_de_charge_id);
 E   DROP INDEX _timescaledb_internal._hyper_2_3_chunk_ix_session_pdc_id;
       _timescaledb_internal            qualicharge    false    310            �           1259    32305 $   _hyper_2_4_chunk_ix_session_id_start    INDEX     |   CREATE UNIQUE INDEX _hyper_2_4_chunk_ix_session_id_start ON _timescaledb_internal._hyper_2_4_chunk USING btree (id, start);
 G   DROP INDEX _timescaledb_internal._hyper_2_4_chunk_ix_session_id_start;
       _timescaledb_internal            qualicharge    false    311    311            �           1259    32304 "   _hyper_2_4_chunk_ix_session_pdc_id    INDEX     |   CREATE INDEX _hyper_2_4_chunk_ix_session_pdc_id ON _timescaledb_internal._hyper_2_4_chunk USING btree (point_de_charge_id);
 E   DROP INDEX _timescaledb_internal._hyper_2_4_chunk_ix_session_pdc_id;
       _timescaledb_internal            qualicharge    false    311            �           1259    32327 $   _hyper_2_5_chunk_ix_session_id_start    INDEX     |   CREATE UNIQUE INDEX _hyper_2_5_chunk_ix_session_id_start ON _timescaledb_internal._hyper_2_5_chunk USING btree (id, start);
 G   DROP INDEX _timescaledb_internal._hyper_2_5_chunk_ix_session_id_start;
       _timescaledb_internal            qualicharge    false    312    312            �           1259    32326 "   _hyper_2_5_chunk_ix_session_pdc_id    INDEX     |   CREATE INDEX _hyper_2_5_chunk_ix_session_pdc_id ON _timescaledb_internal._hyper_2_5_chunk USING btree (point_de_charge_id);
 E   DROP INDEX _timescaledb_internal._hyper_2_5_chunk_ix_session_pdc_id;
       _timescaledb_internal            qualicharge    false    312            �           1259    32349 $   _hyper_2_6_chunk_ix_session_id_start    INDEX     |   CREATE UNIQUE INDEX _hyper_2_6_chunk_ix_session_id_start ON _timescaledb_internal._hyper_2_6_chunk USING btree (id, start);
 G   DROP INDEX _timescaledb_internal._hyper_2_6_chunk_ix_session_id_start;
       _timescaledb_internal            qualicharge    false    313    313            �           1259    32348 "   _hyper_2_6_chunk_ix_session_pdc_id    INDEX     |   CREATE INDEX _hyper_2_6_chunk_ix_session_pdc_id ON _timescaledb_internal._hyper_2_6_chunk USING btree (point_de_charge_id);
 E   DROP INDEX _timescaledb_internal._hyper_2_6_chunk_ix_session_pdc_id;
       _timescaledb_internal            qualicharge    false    313            �           1259    32371 $   _hyper_2_7_chunk_ix_session_id_start    INDEX     |   CREATE UNIQUE INDEX _hyper_2_7_chunk_ix_session_id_start ON _timescaledb_internal._hyper_2_7_chunk USING btree (id, start);
 G   DROP INDEX _timescaledb_internal._hyper_2_7_chunk_ix_session_id_start;
       _timescaledb_internal            qualicharge    false    314    314            �           1259    32370 "   _hyper_2_7_chunk_ix_session_pdc_id    INDEX     |   CREATE INDEX _hyper_2_7_chunk_ix_session_pdc_id ON _timescaledb_internal._hyper_2_7_chunk USING btree (point_de_charge_id);
 E   DROP INDEX _timescaledb_internal._hyper_2_7_chunk_ix_session_pdc_id;
       _timescaledb_internal            qualicharge    false    314            �           1259    21495    idx_city_geometry    INDEX     E   CREATE INDEX idx_city_geometry ON public.city USING gist (geometry);
 %   DROP INDEX public.idx_city_geometry;
       public            qualicharge    false    298    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2            �           1259    23125    idx_department_geometry    INDEX     Q   CREATE INDEX idx_department_geometry ON public.department USING gist (geometry);
 +   DROP INDEX public.idx_department_geometry;
       public            qualicharge    false    299    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2            �           1259    23442    idx_epci_geometry    INDEX     E   CREATE INDEX idx_epci_geometry ON public.epci USING gist (geometry);
 %   DROP INDEX public.idx_epci_geometry;
       public            qualicharge    false    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    300            �           1259    20439    idx_localisation_coordonneesXY    INDEX     c   CREATE INDEX "idx_localisation_coordonneesXY" ON public.localisation USING gist ("coordonneesXY");
 4   DROP INDEX public."idx_localisation_coordonneesXY";
       public            qualicharge    false    287    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2            �           1259    25274    idx_region_geometry    INDEX     I   CREATE INDEX idx_region_geometry ON public.region USING gist (geometry);
 '   DROP INDEX public.idx_region_geometry;
       public            qualicharge    false    301    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2            �           1259    30229    idx_statique_code_insee_commune    INDEX     b   CREATE INDEX idx_statique_code_insee_commune ON public.statique USING btree (code_insee_commune);
 3   DROP INDEX public.idx_statique_code_insee_commune;
       public            qualicharge    false    302            �           1259    30228    idx_statique_coordonneesXY    INDEX     s   CREATE INDEX "idx_statique_coordonneesXY" ON public.statique USING gist (public.st_geomfromewkb("coordonneesXY"));
 0   DROP INDEX public."idx_statique_coordonneesXY";
       public            qualicharge    false    302    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    2    302    2    2    2    2    2    2    2    2    2            �           1259    30230    idx_statique_id_pdc_itinerance    INDEX     g   CREATE UNIQUE INDEX idx_statique_id_pdc_itinerance ON public.statique USING btree (id_pdc_itinerance);
 2   DROP INDEX public.idx_statique_id_pdc_itinerance;
       public            qualicharge    false    302            �           1259    30258 !   ix_activity_native_transaction_id    INDEX     g   CREATE INDEX ix_activity_native_transaction_id ON public.activity USING btree (native_transaction_id);
 5   DROP INDEX public.ix_activity_native_transaction_id;
       public            qualicharge    false    306            �           1259    27937    ix_city_code    INDEX     D   CREATE UNIQUE INDEX ix_city_code ON public.city USING btree (code);
     DROP INDEX public.ix_city_code;
       public            qualicharge    false    298            �           1259    28668    ix_department_code    INDEX     P   CREATE UNIQUE INDEX ix_department_code ON public.department USING btree (code);
 &   DROP INDEX public.ix_department_code;
       public            qualicharge    false    299            �           1259    29887    ix_epci_code    INDEX     D   CREATE UNIQUE INDEX ix_epci_code ON public.epci USING btree (code);
     DROP INDEX public.ix_epci_code;
       public            qualicharge    false    300            �           1259    30406    ix_lateststatus_horodatage    INDEX     Y   CREATE INDEX ix_lateststatus_horodatage ON public.lateststatus USING btree (horodatage);
 .   DROP INDEX public.ix_lateststatus_horodatage;
       public            qualicharge    false    307            �           1259    20601    ix_operationalunit_code    INDEX     Z   CREATE UNIQUE INDEX ix_operationalunit_code ON public.operationalunit USING btree (code);
 +   DROP INDEX public.ix_operationalunit_code;
       public            qualicharge    false    293            �           1259    21489 "   ix_pointdecharge_id_pdc_itinerance    INDEX     p   CREATE UNIQUE INDEX ix_pointdecharge_id_pdc_itinerance ON public.pointdecharge USING btree (id_pdc_itinerance);
 6   DROP INDEX public.ix_pointdecharge_id_pdc_itinerance;
       public            qualicharge    false    290            �           1259    30395    ix_pointdecharge_station_id    INDEX     [   CREATE INDEX ix_pointdecharge_station_id ON public.pointdecharge USING btree (station_id);
 /   DROP INDEX public.ix_pointdecharge_station_id;
       public            qualicharge    false    290            �           1259    29975    ix_region_code    INDEX     H   CREATE UNIQUE INDEX ix_region_code ON public.region USING btree (code);
 "   DROP INDEX public.ix_region_code;
       public            qualicharge    false    301            �           1259    30392    ix_session_id_start    INDEX     S   CREATE UNIQUE INDEX ix_session_id_start ON public.session USING btree (id, start);
 '   DROP INDEX public.ix_session_id_start;
       public            qualicharge    false    291    291            �           1259    30386    ix_session_pdc_id    INDEX     S   CREATE INDEX ix_session_pdc_id ON public.session USING btree (point_de_charge_id);
 %   DROP INDEX public.ix_session_pdc_id;
       public            qualicharge    false    291            �           1259    30396    ix_station_amenageur_id    INDEX     S   CREATE INDEX ix_station_amenageur_id ON public.station USING btree (amenageur_id);
 +   DROP INDEX public.ix_station_amenageur_id;
       public            qualicharge    false    289            �           1259    20501     ix_station_id_station_itinerance    INDEX     l   CREATE UNIQUE INDEX ix_station_id_station_itinerance ON public.station USING btree (id_station_itinerance);
 4   DROP INDEX public.ix_station_id_station_itinerance;
       public            qualicharge    false    289            �           1259    30397    ix_station_operateur_id    INDEX     S   CREATE INDEX ix_station_operateur_id ON public.station USING btree (operateur_id);
 +   DROP INDEX public.ix_station_operateur_id;
       public            qualicharge    false    289            �           1259    30389    ix_status_id_horodatage    INDEX     [   CREATE UNIQUE INDEX ix_status_id_horodatage ON public.status USING btree (id, horodatage);
 +   DROP INDEX public.ix_status_id_horodatage;
       public            qualicharge    false    292    292            �           1259    30383    ix_status_pdc_id    INDEX     Q   CREATE INDEX ix_status_pdc_id ON public.status USING btree (point_de_charge_id);
 $   DROP INDEX public.ix_status_pdc_id;
       public            qualicharge    false    292            e           2620    30364    amenageur audit_trigger_delete    TRIGGER       CREATE TRIGGER audit_trigger_delete AFTER DELETE ON public.amenageur REFERENCING OLD TABLE AS old_table FOR EACH STATEMENT WHEN ((public.get_setting('postgresql_audit.enable_versioning'::text, 'true'::text))::boolean) EXECUTE FUNCTION public.create_activity('{created_at,updated_at}');
 7   DROP TRIGGER audit_trigger_delete ON public.amenageur;
       public          qualicharge    false    1574    1570    285            h           2620    30370    enseigne audit_trigger_delete    TRIGGER       CREATE TRIGGER audit_trigger_delete AFTER DELETE ON public.enseigne REFERENCING OLD TABLE AS old_table FOR EACH STATEMENT WHEN ((public.get_setting('postgresql_audit.enable_versioning'::text, 'true'::text))::boolean) EXECUTE FUNCTION public.create_activity('{created_at,updated_at}');
 6   DROP TRIGGER audit_trigger_delete ON public.enseigne;
       public          qualicharge    false    286    1574    1570            |           2620    30361    group audit_trigger_delete    TRIGGER       CREATE TRIGGER audit_trigger_delete AFTER DELETE ON public."group" REFERENCING OLD TABLE AS old_table FOR EACH STATEMENT WHEN ((public.get_setting('postgresql_audit.enable_versioning'::text, 'true'::text))::boolean) EXECUTE FUNCTION public.create_activity('{created_at,updated_at}');
 5   DROP TRIGGER audit_trigger_delete ON public."group";
       public          qualicharge    false    294    1570    1574            k           2620    30373 !   localisation audit_trigger_delete    TRIGGER     !  CREATE TRIGGER audit_trigger_delete AFTER DELETE ON public.localisation REFERENCING OLD TABLE AS old_table FOR EACH STATEMENT WHEN ((public.get_setting('postgresql_audit.enable_versioning'::text, 'true'::text))::boolean) EXECUTE FUNCTION public.create_activity('{created_at,updated_at}');
 :   DROP TRIGGER audit_trigger_delete ON public.localisation;
       public          qualicharge    false    1574    287    1570            n           2620    30367    operateur audit_trigger_delete    TRIGGER       CREATE TRIGGER audit_trigger_delete AFTER DELETE ON public.operateur REFERENCING OLD TABLE AS old_table FOR EACH STATEMENT WHEN ((public.get_setting('postgresql_audit.enable_versioning'::text, 'true'::text))::boolean) EXECUTE FUNCTION public.create_activity('{created_at,updated_at}');
 7   DROP TRIGGER audit_trigger_delete ON public.operateur;
       public          qualicharge    false    1570    1574    288            t           2620    30379 "   pointdecharge audit_trigger_delete    TRIGGER     "  CREATE TRIGGER audit_trigger_delete AFTER DELETE ON public.pointdecharge REFERENCING OLD TABLE AS old_table FOR EACH STATEMENT WHEN ((public.get_setting('postgresql_audit.enable_versioning'::text, 'true'::text))::boolean) EXECUTE FUNCTION public.create_activity('{created_at,updated_at}');
 ;   DROP TRIGGER audit_trigger_delete ON public.pointdecharge;
       public          qualicharge    false    1574    290    1570            w           2620    30382    session audit_trigger_delete    TRIGGER       CREATE TRIGGER audit_trigger_delete AFTER DELETE ON public.session REFERENCING OLD TABLE AS old_table FOR EACH STATEMENT WHEN ((public.get_setting('postgresql_audit.enable_versioning'::text, 'true'::text))::boolean) EXECUTE FUNCTION public.create_activity('{created_at,updated_at}');
 5   DROP TRIGGER audit_trigger_delete ON public.session;
       public          qualicharge    false    1574    1570    291            q           2620    30376    station audit_trigger_delete    TRIGGER       CREATE TRIGGER audit_trigger_delete AFTER DELETE ON public.station REFERENCING OLD TABLE AS old_table FOR EACH STATEMENT WHEN ((public.get_setting('postgresql_audit.enable_versioning'::text, 'true'::text))::boolean) EXECUTE FUNCTION public.create_activity('{created_at,updated_at}');
 5   DROP TRIGGER audit_trigger_delete ON public.station;
       public          qualicharge    false    1570    289    1574                       2620    30358    user audit_trigger_delete    TRIGGER     $  CREATE TRIGGER audit_trigger_delete AFTER DELETE ON public."user" REFERENCING OLD TABLE AS old_table FOR EACH STATEMENT WHEN ((public.get_setting('postgresql_audit.enable_versioning'::text, 'true'::text))::boolean) EXECUTE FUNCTION public.create_activity('{created_at,updated_at,password}');
 4   DROP TRIGGER audit_trigger_delete ON public."user";
       public          qualicharge    false    295    1574    1570            f           2620    30362    amenageur audit_trigger_insert    TRIGGER       CREATE TRIGGER audit_trigger_insert AFTER INSERT ON public.amenageur REFERENCING NEW TABLE AS new_table FOR EACH STATEMENT WHEN ((public.get_setting('postgresql_audit.enable_versioning'::text, 'true'::text))::boolean) EXECUTE FUNCTION public.create_activity('{created_at,updated_at}');
 7   DROP TRIGGER audit_trigger_insert ON public.amenageur;
       public          qualicharge    false    1570    285    1574            i           2620    30368    enseigne audit_trigger_insert    TRIGGER       CREATE TRIGGER audit_trigger_insert AFTER INSERT ON public.enseigne REFERENCING NEW TABLE AS new_table FOR EACH STATEMENT WHEN ((public.get_setting('postgresql_audit.enable_versioning'::text, 'true'::text))::boolean) EXECUTE FUNCTION public.create_activity('{created_at,updated_at}');
 6   DROP TRIGGER audit_trigger_insert ON public.enseigne;
       public          qualicharge    false    1574    1570    286            }           2620    30359    group audit_trigger_insert    TRIGGER       CREATE TRIGGER audit_trigger_insert AFTER INSERT ON public."group" REFERENCING NEW TABLE AS new_table FOR EACH STATEMENT WHEN ((public.get_setting('postgresql_audit.enable_versioning'::text, 'true'::text))::boolean) EXECUTE FUNCTION public.create_activity('{created_at,updated_at}');
 5   DROP TRIGGER audit_trigger_insert ON public."group";
       public          qualicharge    false    1574    1570    294            l           2620    30371 !   localisation audit_trigger_insert    TRIGGER     !  CREATE TRIGGER audit_trigger_insert AFTER INSERT ON public.localisation REFERENCING NEW TABLE AS new_table FOR EACH STATEMENT WHEN ((public.get_setting('postgresql_audit.enable_versioning'::text, 'true'::text))::boolean) EXECUTE FUNCTION public.create_activity('{created_at,updated_at}');
 :   DROP TRIGGER audit_trigger_insert ON public.localisation;
       public          qualicharge    false    287    1574    1570            o           2620    30365    operateur audit_trigger_insert    TRIGGER       CREATE TRIGGER audit_trigger_insert AFTER INSERT ON public.operateur REFERENCING NEW TABLE AS new_table FOR EACH STATEMENT WHEN ((public.get_setting('postgresql_audit.enable_versioning'::text, 'true'::text))::boolean) EXECUTE FUNCTION public.create_activity('{created_at,updated_at}');
 7   DROP TRIGGER audit_trigger_insert ON public.operateur;
       public          qualicharge    false    1574    288    1570            u           2620    30377 "   pointdecharge audit_trigger_insert    TRIGGER     "  CREATE TRIGGER audit_trigger_insert AFTER INSERT ON public.pointdecharge REFERENCING NEW TABLE AS new_table FOR EACH STATEMENT WHEN ((public.get_setting('postgresql_audit.enable_versioning'::text, 'true'::text))::boolean) EXECUTE FUNCTION public.create_activity('{created_at,updated_at}');
 ;   DROP TRIGGER audit_trigger_insert ON public.pointdecharge;
       public          qualicharge    false    1570    290    1574            x           2620    30380    session audit_trigger_insert    TRIGGER       CREATE TRIGGER audit_trigger_insert AFTER INSERT ON public.session REFERENCING NEW TABLE AS new_table FOR EACH STATEMENT WHEN ((public.get_setting('postgresql_audit.enable_versioning'::text, 'true'::text))::boolean) EXECUTE FUNCTION public.create_activity('{created_at,updated_at}');
 5   DROP TRIGGER audit_trigger_insert ON public.session;
       public          qualicharge    false    1570    1574    291            r           2620    30374    station audit_trigger_insert    TRIGGER       CREATE TRIGGER audit_trigger_insert AFTER INSERT ON public.station REFERENCING NEW TABLE AS new_table FOR EACH STATEMENT WHEN ((public.get_setting('postgresql_audit.enable_versioning'::text, 'true'::text))::boolean) EXECUTE FUNCTION public.create_activity('{created_at,updated_at}');
 5   DROP TRIGGER audit_trigger_insert ON public.station;
       public          qualicharge    false    1570    1574    289            �           2620    30356    user audit_trigger_insert    TRIGGER     $  CREATE TRIGGER audit_trigger_insert AFTER INSERT ON public."user" REFERENCING NEW TABLE AS new_table FOR EACH STATEMENT WHEN ((public.get_setting('postgresql_audit.enable_versioning'::text, 'true'::text))::boolean) EXECUTE FUNCTION public.create_activity('{created_at,updated_at,password}');
 4   DROP TRIGGER audit_trigger_insert ON public."user";
       public          qualicharge    false    1570    295    1574            g           2620    30363    amenageur audit_trigger_update    TRIGGER     5  CREATE TRIGGER audit_trigger_update AFTER UPDATE ON public.amenageur REFERENCING OLD TABLE AS old_table NEW TABLE AS new_table FOR EACH STATEMENT WHEN ((public.get_setting('postgresql_audit.enable_versioning'::text, 'true'::text))::boolean) EXECUTE FUNCTION public.create_activity('{created_at,updated_at}');
 7   DROP TRIGGER audit_trigger_update ON public.amenageur;
       public          qualicharge    false    1570    285    1574            j           2620    30369    enseigne audit_trigger_update    TRIGGER     4  CREATE TRIGGER audit_trigger_update AFTER UPDATE ON public.enseigne REFERENCING OLD TABLE AS old_table NEW TABLE AS new_table FOR EACH STATEMENT WHEN ((public.get_setting('postgresql_audit.enable_versioning'::text, 'true'::text))::boolean) EXECUTE FUNCTION public.create_activity('{created_at,updated_at}');
 6   DROP TRIGGER audit_trigger_update ON public.enseigne;
       public          qualicharge    false    286    1570    1574            ~           2620    30360    group audit_trigger_update    TRIGGER     3  CREATE TRIGGER audit_trigger_update AFTER UPDATE ON public."group" REFERENCING OLD TABLE AS old_table NEW TABLE AS new_table FOR EACH STATEMENT WHEN ((public.get_setting('postgresql_audit.enable_versioning'::text, 'true'::text))::boolean) EXECUTE FUNCTION public.create_activity('{created_at,updated_at}');
 5   DROP TRIGGER audit_trigger_update ON public."group";
       public          qualicharge    false    294    1570    1574            m           2620    30372 !   localisation audit_trigger_update    TRIGGER     8  CREATE TRIGGER audit_trigger_update AFTER UPDATE ON public.localisation REFERENCING OLD TABLE AS old_table NEW TABLE AS new_table FOR EACH STATEMENT WHEN ((public.get_setting('postgresql_audit.enable_versioning'::text, 'true'::text))::boolean) EXECUTE FUNCTION public.create_activity('{created_at,updated_at}');
 :   DROP TRIGGER audit_trigger_update ON public.localisation;
       public          qualicharge    false    1570    1574    287            p           2620    30366    operateur audit_trigger_update    TRIGGER     5  CREATE TRIGGER audit_trigger_update AFTER UPDATE ON public.operateur REFERENCING OLD TABLE AS old_table NEW TABLE AS new_table FOR EACH STATEMENT WHEN ((public.get_setting('postgresql_audit.enable_versioning'::text, 'true'::text))::boolean) EXECUTE FUNCTION public.create_activity('{created_at,updated_at}');
 7   DROP TRIGGER audit_trigger_update ON public.operateur;
       public          qualicharge    false    1574    288    1570            v           2620    30378 "   pointdecharge audit_trigger_update    TRIGGER     9  CREATE TRIGGER audit_trigger_update AFTER UPDATE ON public.pointdecharge REFERENCING OLD TABLE AS old_table NEW TABLE AS new_table FOR EACH STATEMENT WHEN ((public.get_setting('postgresql_audit.enable_versioning'::text, 'true'::text))::boolean) EXECUTE FUNCTION public.create_activity('{created_at,updated_at}');
 ;   DROP TRIGGER audit_trigger_update ON public.pointdecharge;
       public          qualicharge    false    1570    1574    290            y           2620    30381    session audit_trigger_update    TRIGGER     3  CREATE TRIGGER audit_trigger_update AFTER UPDATE ON public.session REFERENCING OLD TABLE AS old_table NEW TABLE AS new_table FOR EACH STATEMENT WHEN ((public.get_setting('postgresql_audit.enable_versioning'::text, 'true'::text))::boolean) EXECUTE FUNCTION public.create_activity('{created_at,updated_at}');
 5   DROP TRIGGER audit_trigger_update ON public.session;
       public          qualicharge    false    1574    1570    291            s           2620    30375    station audit_trigger_update    TRIGGER     3  CREATE TRIGGER audit_trigger_update AFTER UPDATE ON public.station REFERENCING OLD TABLE AS old_table NEW TABLE AS new_table FOR EACH STATEMENT WHEN ((public.get_setting('postgresql_audit.enable_versioning'::text, 'true'::text))::boolean) EXECUTE FUNCTION public.create_activity('{created_at,updated_at}');
 5   DROP TRIGGER audit_trigger_update ON public.station;
       public          qualicharge    false    1574    1570    289            �           2620    30357    user audit_trigger_update    TRIGGER     ;  CREATE TRIGGER audit_trigger_update AFTER UPDATE ON public."user" REFERENCING OLD TABLE AS old_table NEW TABLE AS new_table FOR EACH STATEMENT WHEN ((public.get_setting('postgresql_audit.enable_versioning'::text, 'true'::text))::boolean) EXECUTE FUNCTION public.create_activity('{created_at,updated_at,password}');
 4   DROP TRIGGER audit_trigger_update ON public."user";
       public          qualicharge    false    1570    295    1574            z           2620    30394    session ts_insert_blocker    TRIGGER     �   CREATE TRIGGER ts_insert_blocker BEFORE INSERT ON public.session FOR EACH ROW EXECUTE FUNCTION _timescaledb_functions.insert_blocker();
 2   DROP TRIGGER ts_insert_blocker ON public.session;
       public          qualicharge    false    291    4    4            {           2620    30391    status ts_insert_blocker    TRIGGER     �   CREATE TRIGGER ts_insert_blocker BEFORE INSERT ON public.status FOR EACH ROW EXECUTE FUNCTION _timescaledb_functions.insert_blocker();
 1   DROP TRIGGER ts_insert_blocker ON public.status;
       public          qualicharge    false    4    4    292            W           2606    32424 6   _hyper_1_10_chunk 10_24_status_point_de_charge_id_fkey    FK CONSTRAINT     �   ALTER TABLE ONLY _timescaledb_internal._hyper_1_10_chunk
    ADD CONSTRAINT "10_24_status_point_de_charge_id_fkey" FOREIGN KEY (point_de_charge_id) REFERENCES public.pointdecharge(id);
 q   ALTER TABLE ONLY _timescaledb_internal._hyper_1_10_chunk DROP CONSTRAINT "10_24_status_point_de_charge_id_fkey";
       _timescaledb_internal          qualicharge    false    290    5309    317            X           2606    32436 6   _hyper_1_11_chunk 11_25_status_point_de_charge_id_fkey    FK CONSTRAINT     �   ALTER TABLE ONLY _timescaledb_internal._hyper_1_11_chunk
    ADD CONSTRAINT "11_25_status_point_de_charge_id_fkey" FOREIGN KEY (point_de_charge_id) REFERENCES public.pointdecharge(id);
 q   ALTER TABLE ONLY _timescaledb_internal._hyper_1_11_chunk DROP CONSTRAINT "11_25_status_point_de_charge_id_fkey";
       _timescaledb_internal          qualicharge    false    318    5309    290            Y           2606    32448 6   _hyper_1_12_chunk 12_26_status_point_de_charge_id_fkey    FK CONSTRAINT     �   ALTER TABLE ONLY _timescaledb_internal._hyper_1_12_chunk
    ADD CONSTRAINT "12_26_status_point_de_charge_id_fkey" FOREIGN KEY (point_de_charge_id) REFERENCES public.pointdecharge(id);
 q   ALTER TABLE ONLY _timescaledb_internal._hyper_1_12_chunk DROP CONSTRAINT "12_26_status_point_de_charge_id_fkey";
       _timescaledb_internal          qualicharge    false    290    5309    319            Z           2606    32460 6   _hyper_1_13_chunk 13_27_status_point_de_charge_id_fkey    FK CONSTRAINT     �   ALTER TABLE ONLY _timescaledb_internal._hyper_1_13_chunk
    ADD CONSTRAINT "13_27_status_point_de_charge_id_fkey" FOREIGN KEY (point_de_charge_id) REFERENCES public.pointdecharge(id);
 q   ALTER TABLE ONLY _timescaledb_internal._hyper_1_13_chunk DROP CONSTRAINT "13_27_status_point_de_charge_id_fkey";
       _timescaledb_internal          qualicharge    false    290    320    5309            [           2606    32472 6   _hyper_1_14_chunk 14_28_status_point_de_charge_id_fkey    FK CONSTRAINT     �   ALTER TABLE ONLY _timescaledb_internal._hyper_1_14_chunk
    ADD CONSTRAINT "14_28_status_point_de_charge_id_fkey" FOREIGN KEY (point_de_charge_id) REFERENCES public.pointdecharge(id);
 q   ALTER TABLE ONLY _timescaledb_internal._hyper_1_14_chunk DROP CONSTRAINT "14_28_status_point_de_charge_id_fkey";
       _timescaledb_internal          qualicharge    false    5309    290    321            \           2606    32484 6   _hyper_1_15_chunk 15_29_status_point_de_charge_id_fkey    FK CONSTRAINT     �   ALTER TABLE ONLY _timescaledb_internal._hyper_1_15_chunk
    ADD CONSTRAINT "15_29_status_point_de_charge_id_fkey" FOREIGN KEY (point_de_charge_id) REFERENCES public.pointdecharge(id);
 q   ALTER TABLE ONLY _timescaledb_internal._hyper_1_15_chunk DROP CONSTRAINT "15_29_status_point_de_charge_id_fkey";
       _timescaledb_internal          qualicharge    false    5309    322    290            ]           2606    32496 6   _hyper_1_16_chunk 16_30_status_point_de_charge_id_fkey    FK CONSTRAINT     �   ALTER TABLE ONLY _timescaledb_internal._hyper_1_16_chunk
    ADD CONSTRAINT "16_30_status_point_de_charge_id_fkey" FOREIGN KEY (point_de_charge_id) REFERENCES public.pointdecharge(id);
 q   ALTER TABLE ONLY _timescaledb_internal._hyper_1_16_chunk DROP CONSTRAINT "16_30_status_point_de_charge_id_fkey";
       _timescaledb_internal          qualicharge    false    323    5309    290            ^           2606    32515 6   _hyper_1_17_chunk 17_31_status_point_de_charge_id_fkey    FK CONSTRAINT     �   ALTER TABLE ONLY _timescaledb_internal._hyper_1_17_chunk
    ADD CONSTRAINT "17_31_status_point_de_charge_id_fkey" FOREIGN KEY (point_de_charge_id) REFERENCES public.pointdecharge(id);
 q   ALTER TABLE ONLY _timescaledb_internal._hyper_1_17_chunk DROP CONSTRAINT "17_31_status_point_de_charge_id_fkey";
       _timescaledb_internal          qualicharge    false    5309    290    324            _           2606    32527 6   _hyper_1_18_chunk 18_32_status_point_de_charge_id_fkey    FK CONSTRAINT     �   ALTER TABLE ONLY _timescaledb_internal._hyper_1_18_chunk
    ADD CONSTRAINT "18_32_status_point_de_charge_id_fkey" FOREIGN KEY (point_de_charge_id) REFERENCES public.pointdecharge(id);
 q   ALTER TABLE ONLY _timescaledb_internal._hyper_1_18_chunk DROP CONSTRAINT "18_32_status_point_de_charge_id_fkey";
       _timescaledb_internal          qualicharge    false    325    290    5309            `           2606    32539 6   _hyper_1_19_chunk 19_33_status_point_de_charge_id_fkey    FK CONSTRAINT     �   ALTER TABLE ONLY _timescaledb_internal._hyper_1_19_chunk
    ADD CONSTRAINT "19_33_status_point_de_charge_id_fkey" FOREIGN KEY (point_de_charge_id) REFERENCES public.pointdecharge(id);
 q   ALTER TABLE ONLY _timescaledb_internal._hyper_1_19_chunk DROP CONSTRAINT "19_33_status_point_de_charge_id_fkey";
       _timescaledb_internal          qualicharge    false    290    5309    326            @           2606    32222 /   _hyper_2_1_chunk 1_1_session_created_by_id_fkey    FK CONSTRAINT     �   ALTER TABLE ONLY _timescaledb_internal._hyper_2_1_chunk
    ADD CONSTRAINT "1_1_session_created_by_id_fkey" FOREIGN KEY (created_by_id) REFERENCES public."user"(id);
 j   ALTER TABLE ONLY _timescaledb_internal._hyper_2_1_chunk DROP CONSTRAINT "1_1_session_created_by_id_fkey";
       _timescaledb_internal          qualicharge    false    5324    295    308            A           2606    32227 4   _hyper_2_1_chunk 1_2_session_point_de_charge_id_fkey    FK CONSTRAINT     �   ALTER TABLE ONLY _timescaledb_internal._hyper_2_1_chunk
    ADD CONSTRAINT "1_2_session_point_de_charge_id_fkey" FOREIGN KEY (point_de_charge_id) REFERENCES public.pointdecharge(id);
 o   ALTER TABLE ONLY _timescaledb_internal._hyper_2_1_chunk DROP CONSTRAINT "1_2_session_point_de_charge_id_fkey";
       _timescaledb_internal          qualicharge    false    290    308    5309            B           2606    32232 /   _hyper_2_1_chunk 1_3_session_updated_by_id_fkey    FK CONSTRAINT     �   ALTER TABLE ONLY _timescaledb_internal._hyper_2_1_chunk
    ADD CONSTRAINT "1_3_session_updated_by_id_fkey" FOREIGN KEY (updated_by_id) REFERENCES public."user"(id);
 j   ALTER TABLE ONLY _timescaledb_internal._hyper_2_1_chunk DROP CONSTRAINT "1_3_session_updated_by_id_fkey";
       _timescaledb_internal          qualicharge    false    295    5324    308            a           2606    32551 6   _hyper_1_20_chunk 20_34_status_point_de_charge_id_fkey    FK CONSTRAINT     �   ALTER TABLE ONLY _timescaledb_internal._hyper_1_20_chunk
    ADD CONSTRAINT "20_34_status_point_de_charge_id_fkey" FOREIGN KEY (point_de_charge_id) REFERENCES public.pointdecharge(id);
 q   ALTER TABLE ONLY _timescaledb_internal._hyper_1_20_chunk DROP CONSTRAINT "20_34_status_point_de_charge_id_fkey";
       _timescaledb_internal          qualicharge    false    327    290    5309            b           2606    32563 6   _hyper_1_21_chunk 21_35_status_point_de_charge_id_fkey    FK CONSTRAINT     �   ALTER TABLE ONLY _timescaledb_internal._hyper_1_21_chunk
    ADD CONSTRAINT "21_35_status_point_de_charge_id_fkey" FOREIGN KEY (point_de_charge_id) REFERENCES public.pointdecharge(id);
 q   ALTER TABLE ONLY _timescaledb_internal._hyper_1_21_chunk DROP CONSTRAINT "21_35_status_point_de_charge_id_fkey";
       _timescaledb_internal          qualicharge    false    328    5309    290            c           2606    32597 6   _hyper_1_22_chunk 22_36_status_point_de_charge_id_fkey    FK CONSTRAINT     �   ALTER TABLE ONLY _timescaledb_internal._hyper_1_22_chunk
    ADD CONSTRAINT "22_36_status_point_de_charge_id_fkey" FOREIGN KEY (point_de_charge_id) REFERENCES public.pointdecharge(id);
 q   ALTER TABLE ONLY _timescaledb_internal._hyper_1_22_chunk DROP CONSTRAINT "22_36_status_point_de_charge_id_fkey";
       _timescaledb_internal          qualicharge    false    5309    329    290            d           2606    32652 6   _hyper_1_23_chunk 23_37_status_point_de_charge_id_fkey    FK CONSTRAINT     �   ALTER TABLE ONLY _timescaledb_internal._hyper_1_23_chunk
    ADD CONSTRAINT "23_37_status_point_de_charge_id_fkey" FOREIGN KEY (point_de_charge_id) REFERENCES public.pointdecharge(id);
 q   ALTER TABLE ONLY _timescaledb_internal._hyper_1_23_chunk DROP CONSTRAINT "23_37_status_point_de_charge_id_fkey";
       _timescaledb_internal          qualicharge    false    330    290    5309            C           2606    32244 /   _hyper_2_2_chunk 2_4_session_created_by_id_fkey    FK CONSTRAINT     �   ALTER TABLE ONLY _timescaledb_internal._hyper_2_2_chunk
    ADD CONSTRAINT "2_4_session_created_by_id_fkey" FOREIGN KEY (created_by_id) REFERENCES public."user"(id);
 j   ALTER TABLE ONLY _timescaledb_internal._hyper_2_2_chunk DROP CONSTRAINT "2_4_session_created_by_id_fkey";
       _timescaledb_internal          qualicharge    false    295    309    5324            D           2606    32249 4   _hyper_2_2_chunk 2_5_session_point_de_charge_id_fkey    FK CONSTRAINT     �   ALTER TABLE ONLY _timescaledb_internal._hyper_2_2_chunk
    ADD CONSTRAINT "2_5_session_point_de_charge_id_fkey" FOREIGN KEY (point_de_charge_id) REFERENCES public.pointdecharge(id);
 o   ALTER TABLE ONLY _timescaledb_internal._hyper_2_2_chunk DROP CONSTRAINT "2_5_session_point_de_charge_id_fkey";
       _timescaledb_internal          qualicharge    false    309    5309    290            E           2606    32254 /   _hyper_2_2_chunk 2_6_session_updated_by_id_fkey    FK CONSTRAINT     �   ALTER TABLE ONLY _timescaledb_internal._hyper_2_2_chunk
    ADD CONSTRAINT "2_6_session_updated_by_id_fkey" FOREIGN KEY (updated_by_id) REFERENCES public."user"(id);
 j   ALTER TABLE ONLY _timescaledb_internal._hyper_2_2_chunk DROP CONSTRAINT "2_6_session_updated_by_id_fkey";
       _timescaledb_internal          qualicharge    false    309    5324    295            F           2606    32266 /   _hyper_2_3_chunk 3_7_session_created_by_id_fkey    FK CONSTRAINT     �   ALTER TABLE ONLY _timescaledb_internal._hyper_2_3_chunk
    ADD CONSTRAINT "3_7_session_created_by_id_fkey" FOREIGN KEY (created_by_id) REFERENCES public."user"(id);
 j   ALTER TABLE ONLY _timescaledb_internal._hyper_2_3_chunk DROP CONSTRAINT "3_7_session_created_by_id_fkey";
       _timescaledb_internal          qualicharge    false    5324    310    295            G           2606    32271 4   _hyper_2_3_chunk 3_8_session_point_de_charge_id_fkey    FK CONSTRAINT     �   ALTER TABLE ONLY _timescaledb_internal._hyper_2_3_chunk
    ADD CONSTRAINT "3_8_session_point_de_charge_id_fkey" FOREIGN KEY (point_de_charge_id) REFERENCES public.pointdecharge(id);
 o   ALTER TABLE ONLY _timescaledb_internal._hyper_2_3_chunk DROP CONSTRAINT "3_8_session_point_de_charge_id_fkey";
       _timescaledb_internal          qualicharge    false    290    5309    310            H           2606    32276 /   _hyper_2_3_chunk 3_9_session_updated_by_id_fkey    FK CONSTRAINT     �   ALTER TABLE ONLY _timescaledb_internal._hyper_2_3_chunk
    ADD CONSTRAINT "3_9_session_updated_by_id_fkey" FOREIGN KEY (updated_by_id) REFERENCES public."user"(id);
 j   ALTER TABLE ONLY _timescaledb_internal._hyper_2_3_chunk DROP CONSTRAINT "3_9_session_updated_by_id_fkey";
       _timescaledb_internal          qualicharge    false    295    310    5324            I           2606    32288 0   _hyper_2_4_chunk 4_10_session_created_by_id_fkey    FK CONSTRAINT     �   ALTER TABLE ONLY _timescaledb_internal._hyper_2_4_chunk
    ADD CONSTRAINT "4_10_session_created_by_id_fkey" FOREIGN KEY (created_by_id) REFERENCES public."user"(id);
 k   ALTER TABLE ONLY _timescaledb_internal._hyper_2_4_chunk DROP CONSTRAINT "4_10_session_created_by_id_fkey";
       _timescaledb_internal          qualicharge    false    295    5324    311            J           2606    32293 5   _hyper_2_4_chunk 4_11_session_point_de_charge_id_fkey    FK CONSTRAINT     �   ALTER TABLE ONLY _timescaledb_internal._hyper_2_4_chunk
    ADD CONSTRAINT "4_11_session_point_de_charge_id_fkey" FOREIGN KEY (point_de_charge_id) REFERENCES public.pointdecharge(id);
 p   ALTER TABLE ONLY _timescaledb_internal._hyper_2_4_chunk DROP CONSTRAINT "4_11_session_point_de_charge_id_fkey";
       _timescaledb_internal          qualicharge    false    5309    311    290            K           2606    32298 0   _hyper_2_4_chunk 4_12_session_updated_by_id_fkey    FK CONSTRAINT     �   ALTER TABLE ONLY _timescaledb_internal._hyper_2_4_chunk
    ADD CONSTRAINT "4_12_session_updated_by_id_fkey" FOREIGN KEY (updated_by_id) REFERENCES public."user"(id);
 k   ALTER TABLE ONLY _timescaledb_internal._hyper_2_4_chunk DROP CONSTRAINT "4_12_session_updated_by_id_fkey";
       _timescaledb_internal          qualicharge    false    311    295    5324            L           2606    32310 0   _hyper_2_5_chunk 5_13_session_created_by_id_fkey    FK CONSTRAINT     �   ALTER TABLE ONLY _timescaledb_internal._hyper_2_5_chunk
    ADD CONSTRAINT "5_13_session_created_by_id_fkey" FOREIGN KEY (created_by_id) REFERENCES public."user"(id);
 k   ALTER TABLE ONLY _timescaledb_internal._hyper_2_5_chunk DROP CONSTRAINT "5_13_session_created_by_id_fkey";
       _timescaledb_internal          qualicharge    false    295    5324    312            M           2606    32315 5   _hyper_2_5_chunk 5_14_session_point_de_charge_id_fkey    FK CONSTRAINT     �   ALTER TABLE ONLY _timescaledb_internal._hyper_2_5_chunk
    ADD CONSTRAINT "5_14_session_point_de_charge_id_fkey" FOREIGN KEY (point_de_charge_id) REFERENCES public.pointdecharge(id);
 p   ALTER TABLE ONLY _timescaledb_internal._hyper_2_5_chunk DROP CONSTRAINT "5_14_session_point_de_charge_id_fkey";
       _timescaledb_internal          qualicharge    false    312    290    5309            N           2606    32320 0   _hyper_2_5_chunk 5_15_session_updated_by_id_fkey    FK CONSTRAINT     �   ALTER TABLE ONLY _timescaledb_internal._hyper_2_5_chunk
    ADD CONSTRAINT "5_15_session_updated_by_id_fkey" FOREIGN KEY (updated_by_id) REFERENCES public."user"(id);
 k   ALTER TABLE ONLY _timescaledb_internal._hyper_2_5_chunk DROP CONSTRAINT "5_15_session_updated_by_id_fkey";
       _timescaledb_internal          qualicharge    false    295    5324    312            O           2606    32332 0   _hyper_2_6_chunk 6_16_session_created_by_id_fkey    FK CONSTRAINT     �   ALTER TABLE ONLY _timescaledb_internal._hyper_2_6_chunk
    ADD CONSTRAINT "6_16_session_created_by_id_fkey" FOREIGN KEY (created_by_id) REFERENCES public."user"(id);
 k   ALTER TABLE ONLY _timescaledb_internal._hyper_2_6_chunk DROP CONSTRAINT "6_16_session_created_by_id_fkey";
       _timescaledb_internal          qualicharge    false    5324    295    313            P           2606    32337 5   _hyper_2_6_chunk 6_17_session_point_de_charge_id_fkey    FK CONSTRAINT     �   ALTER TABLE ONLY _timescaledb_internal._hyper_2_6_chunk
    ADD CONSTRAINT "6_17_session_point_de_charge_id_fkey" FOREIGN KEY (point_de_charge_id) REFERENCES public.pointdecharge(id);
 p   ALTER TABLE ONLY _timescaledb_internal._hyper_2_6_chunk DROP CONSTRAINT "6_17_session_point_de_charge_id_fkey";
       _timescaledb_internal          qualicharge    false    5309    290    313            Q           2606    32342 0   _hyper_2_6_chunk 6_18_session_updated_by_id_fkey    FK CONSTRAINT     �   ALTER TABLE ONLY _timescaledb_internal._hyper_2_6_chunk
    ADD CONSTRAINT "6_18_session_updated_by_id_fkey" FOREIGN KEY (updated_by_id) REFERENCES public."user"(id);
 k   ALTER TABLE ONLY _timescaledb_internal._hyper_2_6_chunk DROP CONSTRAINT "6_18_session_updated_by_id_fkey";
       _timescaledb_internal          qualicharge    false    313    295    5324            R           2606    32354 0   _hyper_2_7_chunk 7_19_session_created_by_id_fkey    FK CONSTRAINT     �   ALTER TABLE ONLY _timescaledb_internal._hyper_2_7_chunk
    ADD CONSTRAINT "7_19_session_created_by_id_fkey" FOREIGN KEY (created_by_id) REFERENCES public."user"(id);
 k   ALTER TABLE ONLY _timescaledb_internal._hyper_2_7_chunk DROP CONSTRAINT "7_19_session_created_by_id_fkey";
       _timescaledb_internal          qualicharge    false    5324    314    295            S           2606    32359 5   _hyper_2_7_chunk 7_20_session_point_de_charge_id_fkey    FK CONSTRAINT     �   ALTER TABLE ONLY _timescaledb_internal._hyper_2_7_chunk
    ADD CONSTRAINT "7_20_session_point_de_charge_id_fkey" FOREIGN KEY (point_de_charge_id) REFERENCES public.pointdecharge(id);
 p   ALTER TABLE ONLY _timescaledb_internal._hyper_2_7_chunk DROP CONSTRAINT "7_20_session_point_de_charge_id_fkey";
       _timescaledb_internal          qualicharge    false    5309    290    314            T           2606    32364 0   _hyper_2_7_chunk 7_21_session_updated_by_id_fkey    FK CONSTRAINT     �   ALTER TABLE ONLY _timescaledb_internal._hyper_2_7_chunk
    ADD CONSTRAINT "7_21_session_updated_by_id_fkey" FOREIGN KEY (updated_by_id) REFERENCES public."user"(id);
 k   ALTER TABLE ONLY _timescaledb_internal._hyper_2_7_chunk DROP CONSTRAINT "7_21_session_updated_by_id_fkey";
       _timescaledb_internal          qualicharge    false    314    295    5324            U           2606    32400 4   _hyper_1_8_chunk 8_22_status_point_de_charge_id_fkey    FK CONSTRAINT     �   ALTER TABLE ONLY _timescaledb_internal._hyper_1_8_chunk
    ADD CONSTRAINT "8_22_status_point_de_charge_id_fkey" FOREIGN KEY (point_de_charge_id) REFERENCES public.pointdecharge(id);
 o   ALTER TABLE ONLY _timescaledb_internal._hyper_1_8_chunk DROP CONSTRAINT "8_22_status_point_de_charge_id_fkey";
       _timescaledb_internal          qualicharge    false    315    290    5309            V           2606    32412 4   _hyper_1_9_chunk 9_23_status_point_de_charge_id_fkey    FK CONSTRAINT     �   ALTER TABLE ONLY _timescaledb_internal._hyper_1_9_chunk
    ADD CONSTRAINT "9_23_status_point_de_charge_id_fkey" FOREIGN KEY (point_de_charge_id) REFERENCES public.pointdecharge(id);
 o   ALTER TABLE ONLY _timescaledb_internal._hyper_1_9_chunk DROP CONSTRAINT "9_23_status_point_de_charge_id_fkey";
       _timescaledb_internal          qualicharge    false    316    290    5309            ?           2606    30253 %   activity activity_transaction_id_fkey    FK CONSTRAINT     �   ALTER TABLE ONLY public.activity
    ADD CONSTRAINT activity_transaction_id_fkey FOREIGN KEY (transaction_id) REFERENCES public.transaction(id);
 O   ALTER TABLE ONLY public.activity DROP CONSTRAINT activity_transaction_id_fkey;
       public          qualicharge    false    306    5351    304                       2606    30259 &   amenageur amenageur_created_by_id_fkey    FK CONSTRAINT     �   ALTER TABLE ONLY public.amenageur
    ADD CONSTRAINT amenageur_created_by_id_fkey FOREIGN KEY (created_by_id) REFERENCES public."user"(id);
 P   ALTER TABLE ONLY public.amenageur DROP CONSTRAINT amenageur_created_by_id_fkey;
       public          qualicharge    false    295    5324    285                       2606    30264 &   amenageur amenageur_updated_by_id_fkey    FK CONSTRAINT     �   ALTER TABLE ONLY public.amenageur
    ADD CONSTRAINT amenageur_updated_by_id_fkey FOREIGN KEY (updated_by_id) REFERENCES public."user"(id);
 P   ALTER TABLE ONLY public.amenageur DROP CONSTRAINT amenageur_updated_by_id_fkey;
       public          qualicharge    false    295    285    5324            <           2606    29984    city city_department_id_fkey    FK CONSTRAINT     �   ALTER TABLE ONLY public.city
    ADD CONSTRAINT city_department_id_fkey FOREIGN KEY (department_id) REFERENCES public.department(id);
 F   ALTER TABLE ONLY public.city DROP CONSTRAINT city_department_id_fkey;
       public          qualicharge    false    298    299    5336            =           2606    29989    city city_epci_id_fkey    FK CONSTRAINT     t   ALTER TABLE ONLY public.city
    ADD CONSTRAINT city_epci_id_fkey FOREIGN KEY (epci_id) REFERENCES public.epci(id);
 @   ALTER TABLE ONLY public.city DROP CONSTRAINT city_epci_id_fkey;
       public          qualicharge    false    298    300    5340            >           2606    29994 $   department department_region_id_fkey    FK CONSTRAINT     �   ALTER TABLE ONLY public.department
    ADD CONSTRAINT department_region_id_fkey FOREIGN KEY (region_id) REFERENCES public.region(id);
 N   ALTER TABLE ONLY public.department DROP CONSTRAINT department_region_id_fkey;
       public          qualicharge    false    5346    301    299                        2606    30269 $   enseigne enseigne_created_by_id_fkey    FK CONSTRAINT     �   ALTER TABLE ONLY public.enseigne
    ADD CONSTRAINT enseigne_created_by_id_fkey FOREIGN KEY (created_by_id) REFERENCES public."user"(id);
 N   ALTER TABLE ONLY public.enseigne DROP CONSTRAINT enseigne_created_by_id_fkey;
       public          qualicharge    false    286    295    5324            !           2606    30274 $   enseigne enseigne_updated_by_id_fkey    FK CONSTRAINT     �   ALTER TABLE ONLY public.enseigne
    ADD CONSTRAINT enseigne_updated_by_id_fkey FOREIGN KEY (updated_by_id) REFERENCES public."user"(id);
 N   ALTER TABLE ONLY public.enseigne DROP CONSTRAINT enseigne_updated_by_id_fkey;
       public          qualicharge    false    295    5324    286            4           2606    30279    group group_created_by_id_fkey    FK CONSTRAINT     �   ALTER TABLE ONLY public."group"
    ADD CONSTRAINT group_created_by_id_fkey FOREIGN KEY (created_by_id) REFERENCES public."user"(id);
 J   ALTER TABLE ONLY public."group" DROP CONSTRAINT group_created_by_id_fkey;
       public          qualicharge    false    294    295    5324            5           2606    30284    group group_updated_by_id_fkey    FK CONSTRAINT     �   ALTER TABLE ONLY public."group"
    ADD CONSTRAINT group_updated_by_id_fkey FOREIGN KEY (updated_by_id) REFERENCES public."user"(id);
 J   ALTER TABLE ONLY public."group" DROP CONSTRAINT group_updated_by_id_fkey;
       public          qualicharge    false    295    294    5324            8           2606    20632 7   groupoperationalunit groupoperationalunit_group_id_fkey    FK CONSTRAINT     �   ALTER TABLE ONLY public.groupoperationalunit
    ADD CONSTRAINT groupoperationalunit_group_id_fkey FOREIGN KEY (group_id) REFERENCES public."group"(id);
 a   ALTER TABLE ONLY public.groupoperationalunit DROP CONSTRAINT groupoperationalunit_group_id_fkey;
       public          qualicharge    false    5320    294    296            9           2606    20637 B   groupoperationalunit groupoperationalunit_operational_unit_id_fkey    FK CONSTRAINT     �   ALTER TABLE ONLY public.groupoperationalunit
    ADD CONSTRAINT groupoperationalunit_operational_unit_id_fkey FOREIGN KEY (operational_unit_id) REFERENCES public.operationalunit(id);
 l   ALTER TABLE ONLY public.groupoperationalunit DROP CONSTRAINT groupoperationalunit_operational_unit_id_fkey;
       public          qualicharge    false    293    5316    296            "           2606    30289 ,   localisation localisation_created_by_id_fkey    FK CONSTRAINT     �   ALTER TABLE ONLY public.localisation
    ADD CONSTRAINT localisation_created_by_id_fkey FOREIGN KEY (created_by_id) REFERENCES public."user"(id);
 V   ALTER TABLE ONLY public.localisation DROP CONSTRAINT localisation_created_by_id_fkey;
       public          qualicharge    false    5324    295    287            #           2606    30294 ,   localisation localisation_updated_by_id_fkey    FK CONSTRAINT     �   ALTER TABLE ONLY public.localisation
    ADD CONSTRAINT localisation_updated_by_id_fkey FOREIGN KEY (updated_by_id) REFERENCES public."user"(id);
 V   ALTER TABLE ONLY public.localisation DROP CONSTRAINT localisation_updated_by_id_fkey;
       public          qualicharge    false    295    287    5324            $           2606    30299 &   operateur operateur_created_by_id_fkey    FK CONSTRAINT     �   ALTER TABLE ONLY public.operateur
    ADD CONSTRAINT operateur_created_by_id_fkey FOREIGN KEY (created_by_id) REFERENCES public."user"(id);
 P   ALTER TABLE ONLY public.operateur DROP CONSTRAINT operateur_created_by_id_fkey;
       public          qualicharge    false    288    295    5324            %           2606    30304 &   operateur operateur_updated_by_id_fkey    FK CONSTRAINT     �   ALTER TABLE ONLY public.operateur
    ADD CONSTRAINT operateur_updated_by_id_fkey FOREIGN KEY (updated_by_id) REFERENCES public."user"(id);
 P   ALTER TABLE ONLY public.operateur DROP CONSTRAINT operateur_updated_by_id_fkey;
       public          qualicharge    false    288    5324    295            -           2606    30309 .   pointdecharge pointdecharge_created_by_id_fkey    FK CONSTRAINT     �   ALTER TABLE ONLY public.pointdecharge
    ADD CONSTRAINT pointdecharge_created_by_id_fkey FOREIGN KEY (created_by_id) REFERENCES public."user"(id);
 X   ALTER TABLE ONLY public.pointdecharge DROP CONSTRAINT pointdecharge_created_by_id_fkey;
       public          qualicharge    false    5324    290    295            .           2606    20519 +   pointdecharge pointdecharge_station_id_fkey    FK CONSTRAINT     �   ALTER TABLE ONLY public.pointdecharge
    ADD CONSTRAINT pointdecharge_station_id_fkey FOREIGN KEY (station_id) REFERENCES public.station(id);
 U   ALTER TABLE ONLY public.pointdecharge DROP CONSTRAINT pointdecharge_station_id_fkey;
       public          qualicharge    false    289    5305    290            /           2606    30314 .   pointdecharge pointdecharge_updated_by_id_fkey    FK CONSTRAINT     �   ALTER TABLE ONLY public.pointdecharge
    ADD CONSTRAINT pointdecharge_updated_by_id_fkey FOREIGN KEY (updated_by_id) REFERENCES public."user"(id);
 X   ALTER TABLE ONLY public.pointdecharge DROP CONSTRAINT pointdecharge_updated_by_id_fkey;
       public          qualicharge    false    5324    295    290            0           2606    30319 "   session session_created_by_id_fkey    FK CONSTRAINT     �   ALTER TABLE ONLY public.session
    ADD CONSTRAINT session_created_by_id_fkey FOREIGN KEY (created_by_id) REFERENCES public."user"(id);
 L   ALTER TABLE ONLY public.session DROP CONSTRAINT session_created_by_id_fkey;
       public          qualicharge    false    295    291    5324            1           2606    20547 '   session session_point_de_charge_id_fkey    FK CONSTRAINT     �   ALTER TABLE ONLY public.session
    ADD CONSTRAINT session_point_de_charge_id_fkey FOREIGN KEY (point_de_charge_id) REFERENCES public.pointdecharge(id);
 Q   ALTER TABLE ONLY public.session DROP CONSTRAINT session_point_de_charge_id_fkey;
       public          qualicharge    false    5309    290    291            2           2606    30324 "   session session_updated_by_id_fkey    FK CONSTRAINT     �   ALTER TABLE ONLY public.session
    ADD CONSTRAINT session_updated_by_id_fkey FOREIGN KEY (updated_by_id) REFERENCES public."user"(id);
 L   ALTER TABLE ONLY public.session DROP CONSTRAINT session_updated_by_id_fkey;
       public          qualicharge    false    291    295    5324            &           2606    30004 !   station station_amenageur_id_fkey    FK CONSTRAINT     �   ALTER TABLE ONLY public.station
    ADD CONSTRAINT station_amenageur_id_fkey FOREIGN KEY (amenageur_id) REFERENCES public.amenageur(id) ON DELETE SET NULL;
 K   ALTER TABLE ONLY public.station DROP CONSTRAINT station_amenageur_id_fkey;
       public          qualicharge    false    285    289    5287            '           2606    30329 "   station station_created_by_id_fkey    FK CONSTRAINT     �   ALTER TABLE ONLY public.station
    ADD CONSTRAINT station_created_by_id_fkey FOREIGN KEY (created_by_id) REFERENCES public."user"(id);
 L   ALTER TABLE ONLY public.station DROP CONSTRAINT station_created_by_id_fkey;
       public          qualicharge    false    5324    289    295            (           2606    30014     station station_enseigne_id_fkey    FK CONSTRAINT     �   ALTER TABLE ONLY public.station
    ADD CONSTRAINT station_enseigne_id_fkey FOREIGN KEY (enseigne_id) REFERENCES public.enseigne(id) ON DELETE SET NULL;
 J   ALTER TABLE ONLY public.station DROP CONSTRAINT station_enseigne_id_fkey;
       public          qualicharge    false    286    289    5291            )           2606    30019 $   station station_localisation_id_fkey    FK CONSTRAINT     �   ALTER TABLE ONLY public.station
    ADD CONSTRAINT station_localisation_id_fkey FOREIGN KEY (localisation_id) REFERENCES public.localisation(id) ON DELETE SET NULL;
 N   ALTER TABLE ONLY public.station DROP CONSTRAINT station_localisation_id_fkey;
       public          qualicharge    false    289    287    5296            *           2606    29999 !   station station_operateur_id_fkey    FK CONSTRAINT     �   ALTER TABLE ONLY public.station
    ADD CONSTRAINT station_operateur_id_fkey FOREIGN KEY (operateur_id) REFERENCES public.operateur(id) ON DELETE SET NULL;
 K   ALTER TABLE ONLY public.station DROP CONSTRAINT station_operateur_id_fkey;
       public          qualicharge    false    289    5300    288            +           2606    30009 (   station station_operational_unit_id_fkey    FK CONSTRAINT     �   ALTER TABLE ONLY public.station
    ADD CONSTRAINT station_operational_unit_id_fkey FOREIGN KEY (operational_unit_id) REFERENCES public.operationalunit(id) ON DELETE SET NULL;
 R   ALTER TABLE ONLY public.station DROP CONSTRAINT station_operational_unit_id_fkey;
       public          qualicharge    false    289    293    5316            ,           2606    30334 "   station station_updated_by_id_fkey    FK CONSTRAINT     �   ALTER TABLE ONLY public.station
    ADD CONSTRAINT station_updated_by_id_fkey FOREIGN KEY (updated_by_id) REFERENCES public."user"(id);
 L   ALTER TABLE ONLY public.station DROP CONSTRAINT station_updated_by_id_fkey;
       public          qualicharge    false    289    5324    295            3           2606    20583 %   status status_point_de_charge_id_fkey    FK CONSTRAINT     �   ALTER TABLE ONLY public.status
    ADD CONSTRAINT status_point_de_charge_id_fkey FOREIGN KEY (point_de_charge_id) REFERENCES public.pointdecharge(id);
 O   ALTER TABLE ONLY public.status DROP CONSTRAINT status_point_de_charge_id_fkey;
       public          qualicharge    false    292    5309    290            6           2606    30339    user user_created_by_id_fkey    FK CONSTRAINT     �   ALTER TABLE ONLY public."user"
    ADD CONSTRAINT user_created_by_id_fkey FOREIGN KEY (created_by_id) REFERENCES public."user"(id);
 H   ALTER TABLE ONLY public."user" DROP CONSTRAINT user_created_by_id_fkey;
       public          qualicharge    false    295    5324    295            7           2606    30344    user user_updated_by_id_fkey    FK CONSTRAINT     �   ALTER TABLE ONLY public."user"
    ADD CONSTRAINT user_updated_by_id_fkey FOREIGN KEY (updated_by_id) REFERENCES public."user"(id);
 H   ALTER TABLE ONLY public."user" DROP CONSTRAINT user_updated_by_id_fkey;
       public          qualicharge    false    5324    295    295            :           2606    20647 !   usergroup usergroup_group_id_fkey    FK CONSTRAINT     �   ALTER TABLE ONLY public.usergroup
    ADD CONSTRAINT usergroup_group_id_fkey FOREIGN KEY (group_id) REFERENCES public."group"(id);
 K   ALTER TABLE ONLY public.usergroup DROP CONSTRAINT usergroup_group_id_fkey;
       public          qualicharge    false    5320    297    294            ;           2606    20652     usergroup usergroup_user_id_fkey    FK CONSTRAINT     �   ALTER TABLE ONLY public.usergroup
    ADD CONSTRAINT usergroup_user_id_fkey FOREIGN KEY (user_id) REFERENCES public."user"(id);
 J   ALTER TABLE ONLY public.usergroup DROP CONSTRAINT usergroup_user_id_fkey;
       public          qualicharge    false    295    5324    297           