-- Account table
CREATE TABLE IF NOT EXISTS accounts (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    email VARCHAR(255) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    role VARCHAR(50) DEFAULT 'user'
);

-- Projects table
CREATE TYPE project_status_type AS ENUM ('open', 'close');
CREATE TYPE project_files_status_type AS ENUM ('processing', 'success', 'error');

CREATE TABLE projects (
    id SERIAL PRIMARY KEY,
    name VARCHAR NOT NULL,
    created_at TIMESTAMP NOT NULL DEFAULT NOW(),
    status project_status_type NOT NULL DEFAULT 'open',
    count_of_files INTEGER NOT NULL DEFAULT 0,
    status_files project_files_status_type NOT NULL DEFAULT 'success'
);

CREATE INDEX idx_projects_status ON projects(status);
CREATE INDEX idx_projects_created_at ON projects(created_at);

CREATE SEQUENCE IF NOT EXISTS project_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;

ALTER SEQUENCE project_id_seq OWNED BY projects.id;

-- Project files table
CREATE TYPE file_status_type AS ENUM ('processing', 'success', 'error');

CREATE TABLE project_files (
    id SERIAL PRIMARY KEY,
    project_id INTEGER NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
    filename VARCHAR NOT NULL,
    s3_path VARCHAR NOT NULL,
    s3_url VARCHAR NOT NULL,
    s3_icon_path VARCHAR NOT NULL,
    s3_icon_url VARCHAR NOT NULL,
    s3_txt_path VARCHAR NOT NULL,
    s3_txt_url VARCHAR NOT NULL,
    s3_report_path VARCHAR DEFAULT NULL,
    s3_report_url VARCHAR DEFAULT NULL,
    status file_status_type NOT NULL DEFAULT 'processing'
);

CREATE INDEX idx_project_files_project_id ON project_files(project_id);
CREATE INDEX idx_project_files_status ON project_files(status);
CREATE INDEX idx_project_files_composite ON project_files(project_id, status);

CREATE SEQUENCE IF NOT EXISTS project_files_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;

ALTER SEQUENCE project_files_id_seq OWNED BY project_files.id;

-- File (photo) defects table
CREATE TABLE file_defects (
    id SERIAL PRIMARY KEY,
    file_id INTEGER NOT NULL REFERENCES project_files(id) ON DELETE CASCADE,
    class_id INTEGER NOT NULL,
    count INTEGER DEFAULT 1
);

ALTER TABLE project_files ADD COLUMN defect_count INTEGER DEFAULT 0;

-- Триггерная функция для обновления проектов
CREATE OR REPLACE FUNCTION update_project_files_stats()
RETURNS TRIGGER AS $$
BEGIN
    -- Обновляем count_of_files
    UPDATE projects
    SET count_of_files = (
        SELECT COUNT(*)
        FROM project_files
        WHERE project_id = COALESCE(NEW.project_id, OLD.project_id)
    )
    WHERE id = COALESCE(NEW.project_id, OLD.project_id);

    -- Обновляем status_files
    WITH file_stats AS (
        SELECT
            project_id,
            COUNT(*) FILTER (WHERE status = 'error') as error_count,
            COUNT(*) FILTER (WHERE status = 'processing') as processing_count,
            COUNT(*) as total
        FROM project_files
        WHERE project_id = COALESCE(NEW.project_id, OLD.project_id)
        GROUP BY project_id
    )
    UPDATE projects p
    SET status_files = CASE
        WHEN fs.error_count > 0 THEN 'error'::project_files_status_type
        WHEN fs.processing_count > 0 THEN 'processing'::project_files_status_type
        ELSE 'success'::project_files_status_type
    END
    FROM file_stats fs
    WHERE p.id = fs.project_id;

    RETURN NULL;
END;
$$ LANGUAGE plpgsql;

-- Триггеры для всех операций
CREATE TRIGGER update_project_stats
AFTER INSERT OR UPDATE OR DELETE ON project_files
FOR EACH ROW EXECUTE FUNCTION update_project_files_stats();
