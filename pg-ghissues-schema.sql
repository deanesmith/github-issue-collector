
------------ Create database ------------
/*
CREATE DATABASE ghissues
    WITH 
    OWNER = postgres
    ENCODING = 'UTF8'
    LC_COLLATE = 'en_US.UTF8'
    LC_CTYPE = 'en_US.UTF8'
    CONNECTION LIMIT = -1;
*/
------------ Create repos table ------------

CREATE TABLE public.repos
(
	repo_id serial primary key NOT NULL,
    org varchar(256) NOT NULL,
    name varchar(256) NOT NULL,
	repo_url varchar(512) NOT NULL
)
WITH (
    OIDS = FALSE
)
TABLESPACE pg_default;

ALTER TABLE public.repos
    OWNER to postgres;

GRANT SELECT ON TABLE public.repos TO ghissuesuser WITH GRANT OPTION;

------------ Create users table ------------

CREATE TABLE public.users
(
	user_id bigint primary key NOT NULL,
    login character varying(50) COLLATE pg_catalog."default" NOT NULL
)
WITH (
    OIDS = FALSE
)
TABLESPACE pg_default;

ALTER TABLE public.users
    OWNER to postgres;

GRANT SELECT ON TABLE public.users TO ghissuesuser WITH GRANT OPTION;

------------ Create issues table ------------

CREATE TABLE public.issues
(
    issue_id bigint unique NOT NULL,
	repo_id bigint NOT NULL,
    node_id character varying(256) COLLATE pg_catalog."default" NOT NULL,
    "number" integer NOT NULL,
	user_id bigint NOT NULL,
    state character varying(8) COLLATE pg_catalog."default" NOT NULL,
    pull_request smallint,
    created_at timestamp,
    closed_at timestamp,
    json_data json,
    CONSTRAINT issues_pkey PRIMARY KEY (issue_id)
)
WITH (
    OIDS = FALSE
)
TABLESPACE pg_default;

ALTER TABLE public.issues
    OWNER to postgres;

ALTER TABLE public.issues
    ADD CONSTRAINT fk_repos_issues_repo_id FOREIGN KEY (repo_id)
    REFERENCES public.repos (repo_id) MATCH SIMPLE
    ON UPDATE NO ACTION
    ON DELETE CASCADE;
CREATE INDEX fki_fk_repos_issues_repo_id
    ON public.repos(repo_id);	
	
GRANT SELECT ON TABLE public.issues TO ghissuesuser WITH GRANT OPTION;
	
------------ Create labels table ------------

CREATE TABLE public.labels
(
	id serial primary key NOT NULL,
    label_id bigint NOT NULL,
    node_id character varying(256) COLLATE pg_catalog."default" NOT NULL,
    issue_id bigint NOT NULL,
    name character varying(50) COLLATE pg_catalog."default" NOT NULL
)
WITH (
    OIDS = FALSE
)
TABLESPACE pg_default;

ALTER TABLE public.labels
    OWNER to postgres;

ALTER TABLE public.labels
    ADD CONSTRAINT fk_labels_issues_issue_id FOREIGN KEY (issue_id)
    REFERENCES public.issues (issue_id) MATCH SIMPLE
    ON UPDATE NO ACTION
    ON DELETE CASCADE;
CREATE INDEX fki_fk_labels_issues_issue_id
    ON public.labels(issue_id);	

GRANT SELECT ON TABLE public.labels TO ghissuesuser WITH GRANT OPTION;

------------ Add tablefunc for crosstabs ------------

CREATE EXTENSION tablefunc;

------------ Add repos to repos table ------------

INSERT INTO repos(org, name, repo_url) VALUES('jenkins-x', 'jx', 'https://github.com/jenkins-x/jx');