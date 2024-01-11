create table if not exists public.delays
(
    id          integer not null
        constraint delays_pk
            primary key,
    column_name integer,
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
    date          date,
    weather_code  integer,
    temperature   double precision,
    daylight      double precision,
    precipitation double precision,
    wind          double precision
);

alter table public.weather
    owner to postgres;
