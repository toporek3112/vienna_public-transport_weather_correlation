create table if not exists public.delays
(
    id          integer not null,
    title       varchar(255),
    lines       varchar,
    stations    varchar,
    start       timestamp,
    "end"       timestamp
);

alter table public.delays
    owner to postgres;

create table if not exists public.weather
(
    id            integer not null
        constraint weather_pk
            primary key,
    time          timestamp,
    weather_code  integer,
    temperature   double precision,
    daylight      double precision,
    precipitation double precision,
    wind          double precision
);

alter table public.weather
    owner to postgres;

create table if not exists public.stops
(
    id        integer not null
        constraint stops_pk
            primary key,
    name      varchar,
    longitude double precision,
    latitude  double precision
);

alter table public.stops
    owner to postgres;

    create table if not exists public.delays_manual
(
    id       text,
    title    text,
    behoben  boolean,
    lines    text,
    stations text,
    start    timestamp,
    "end"    timestamp
);

alter table public.delays_manual
    owner to postgres;

create table if not exists public.weather_manual
(
    id                   bigint,
    time                 timestamp,
    temperature_2m       double precision,
    relative_humidity_2m double precision,
    wind_speed_10m       double precision
);

alter table public.weather_manual
    owner to postgres;

create index if not exists ix_weather_manual_id
    on public.weather_manual (id);

create table if not exists public.stops_manual
(
    id        bigint,
    name      text,
    longitude double precision,
    latitude  double precision
);

alter table public.stops_manual
    owner to postgres;

