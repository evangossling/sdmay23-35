USE aps_dataset;

# models / objects
CREATE TABLE IF NOT EXISTS authors (
	id int AUTO_INCREMENT NOT NULL primary key,
	name varchar(255) NOT NULL,
    type varchar(255),
    firstname varchar(255),
    surname varchar(255)
);

CREATE TABLE IF NOT EXISTS places (
   id int AUTO_INCREMENT NOT NULL primary key,
   name text NOT NULL, #should be unique - verified by inserters
   lon int,
   lat int
);

CREATE TABLE IF NOT EXISTS journals (
	id int AUTO_INCREMENT NOT NULL primary key,
    journalID varchar(255) unique NOT NULL,
    abbreviatedName text,
    name text NOT NULL
);

CREATE TABLE IF NOT EXISTS publishers (
	id int AUTO_INCREMENT NOT NULL primary key,
    name varchar(255) NOT NULL UNIQUE
);

CREATE TABLE IF NOT EXISTS papers (
	id int AUTO_INCREMENT NOT NULL primary key,
	doi varchar(255) NOT NULL unique,
    title text NOT NULL,
    title_format varchar(255) NOT NULL,
    issue int,
    volume int,
    pageStart varchar(255),
    hadArticleID boolean,
    date DATE,
    numpages int,
    articleType varchar(255),
    classificationSchemes json,
	rights json,
    #foreign
  --   rightsID int,
	journalID int,
	publisherID int,
   --  FOREIGN KEY (rightsID) REFERENCES rights(id),
    FOREIGN KEY (journalID) REFERENCES journals(id),
    FOREIGN KEY (publisherID) REFERENCES publishers(id)
);

# join tables
CREATE TABLE IF NOT EXISTS paper_author (
	paperID int not null,
    authorID int not null,
    primary key (paperID, authorID),
    FOREIGN KEY (paperID) REFERENCES papers(id),
    FOREIGN KEY (authorID) REFERENCES authors(id)
);

CREATE TABLE IF NOT EXISTS paper_place (
	paperID int not null,
    placeID int not null,
    primary key (paperID, placeID),
    FOREIGN KEY (paperID) REFERENCES papers(id),
    FOREIGN KEY (placeID) REFERENCES places(id)
);

CREATE TABLE IF NOT EXISTS author_place (
	authorID int not null,
    placeID int not null,
    primary key (authorID, placeID),
    FOREIGN KEY (authorID) REFERENCES authors(id),
    FOREIGN KEY (placeID) REFERENCES places(id)
);

-- CREATE TABLE IF NOT EXISTS paper_subject (
-- 	paperID int not null,
--     subjectID int not null,
--     primary key (paperID, subjectID),
--     FOREIGN KEY (paperID) REFERENCES papers(id),
--     FOREIGN KEY (subjectID) REFERENCES subjects(id)
-- );

-- CREATE TABLE IF NOT EXISTS right_license (
-- 	rightID int not null,
--     licenseID int not null,
--     primary key (rightID, licenseID),
--     FOREIGN KEY (rightID) REFERENCES rights(id),
--     FOREIGN KEY (licenseID) REFERENCES licences(id)
-- );

-- CREATE TABLE IF NOT EXISTS subjects (
-- 	id int AUTO_INCREMENT NOT NULL primary key,
-- 	subID varchar(255) NOT NULL unique,
--     label varchar(255) NOT NULL
-- );

-- CREATE TABLE IF NOT EXISTS licenses (
-- 	id int AUTO_INCREMENT NOT NULL primary key,
-- 	type varchar(255) NOT NULL,
--     url varchar(255) NOT NULL UNIQUE,
--     usageStatement text,
--     usageSatementFormat varchar(255)
-- );

-- CREATE TABLE IF NOT EXISTS rights (
-- 	id int AUTO_INCREMENT NOT NULL primary key,
--     rightsStatement varchar(255),
--     copyrightYear int,
--     creativeCommons bool
-- );