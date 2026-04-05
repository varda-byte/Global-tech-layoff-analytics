-- ================================================
-- Global Tech Layoff Analytics
-- Complete SQL Queries File
-- ================================================

USE layoff_analytics;

-- ------------------------------------------------
-- BASIC QUERIES (1-5)
-- ------------------------------------------------

-- Query 1: Top 10 companies with most layoffs
SELECT c.company_name, 
       SUM(e.employees_laid_off) AS total_laid_off
FROM layoff_events e
JOIN companies c ON e.company_id = c.company_id
WHERE e.employees_laid_off IS NOT NULL
GROUP BY c.company_name
ORDER BY total_laid_off DESC
LIMIT 10;

-- Query 2: Total layoffs per industry
SELECT i.industry_name,
       SUM(e.employees_laid_off) AS total_laid_off,
       COUNT(*) AS total_events
FROM layoff_events e
JOIN companies c ON e.company_id = c.company_id
JOIN industries i ON c.industry_id = i.industry_id
WHERE e.employees_laid_off IS NOT NULL
GROUP BY i.industry_name
ORDER BY total_laid_off DESC;

-- Query 3: Year wise layoff trend
SELECT YEAR(layoff_date) AS year,
       SUM(employees_laid_off) AS total_laid_off,
       COUNT(*) AS total_events
FROM layoff_events
WHERE layoff_date IS NOT NULL
GROUP BY YEAR(layoff_date)
ORDER BY year;

-- Query 4: Country wise layoffs
SELECT l.country,
       SUM(e.employees_laid_off) AS total_laid_off,
       COUNT(*) AS total_events
FROM layoff_events e
JOIN companies c ON e.company_id = c.company_id
JOIN locations l ON c.location_id = l.location_id
WHERE e.employees_laid_off IS NOT NULL
GROUP BY l.country
ORDER BY total_laid_off DESC;

-- Query 5: Companies that shut down completely (100% layoff)
SELECT c.company_name,
       e.employees_laid_off,
       e.percentage_laid_off,
       e.layoff_date
FROM layoff_events e
JOIN companies c ON e.company_id = c.company_id
WHERE e.percentage_laid_off = 1
ORDER BY e.employees_laid_off DESC;

-- ------------------------------------------------
-- INTERMEDIATE QUERIES (6-10)
-- ------------------------------------------------

-- Query 6: Month wise layoff trend
SELECT DATE_FORMAT(layoff_date, '%Y-%m') AS month,
       SUM(employees_laid_off) AS total_laid_off
FROM layoff_events
WHERE layoff_date IS NOT NULL
AND employees_laid_off IS NOT NULL
GROUP BY DATE_FORMAT(layoff_date, '%Y-%m')
ORDER BY month;

-- Query 7: Layoffs by funding stage
SELECT e.stage,
       COUNT(*) AS total_events,
       SUM(e.employees_laid_off) AS total_laid_off,
       AVG(e.percentage_laid_off) AS avg_percentage
FROM layoff_events e
WHERE e.stage IS NOT NULL
GROUP BY e.stage
ORDER BY total_laid_off DESC;

-- Query 8: Top 5 industries per year
SELECT year, industry_name, total_laid_off
FROM (
    SELECT YEAR(e.layoff_date) AS year,
           i.industry_name,
           SUM(e.employees_laid_off) AS total_laid_off,
           RANK() OVER (PARTITION BY YEAR(e.layoff_date) 
                        ORDER BY SUM(e.employees_laid_off) DESC) AS rnk
    FROM layoff_events e
    JOIN companies c ON e.company_id = c.company_id
    JOIN industries i ON c.industry_id = i.industry_id
    WHERE e.employees_laid_off IS NOT NULL
    AND e.layoff_date IS NOT NULL
    GROUP BY YEAR(e.layoff_date), i.industry_name
) ranked
WHERE rnk <= 5
ORDER BY year, rnk;

-- Query 9: Average layoff percentage by industry
SELECT i.industry_name,
       ROUND(AVG(e.percentage_laid_off) * 100, 2) AS avg_percentage,
       COUNT(*) AS total_companies
FROM layoff_events e
JOIN companies c ON e.company_id = c.company_id
JOIN industries i ON c.industry_id = i.industry_id
WHERE e.percentage_laid_off IS NOT NULL
GROUP BY i.industry_name
ORDER BY avg_percentage DESC;

-- Query 10: Companies with multiple layoff rounds
SELECT c.company_name,
       COUNT(*) AS layoff_rounds,
       SUM(e.employees_laid_off) AS total_laid_off
FROM layoff_events e
JOIN companies c ON e.company_id = c.company_id
WHERE e.employees_laid_off IS NOT NULL
GROUP BY c.company_name
HAVING layoff_rounds > 1
ORDER BY layoff_rounds DESC;

-- ------------------------------------------------
-- ADVANCED QUERIES (11-15)
-- ------------------------------------------------

-- Query 11: Running total of layoffs over time
SELECT layoff_date,
       employees_laid_off,
       SUM(employees_laid_off) OVER (ORDER BY layoff_date) AS running_total
FROM layoff_events
WHERE layoff_date IS NOT NULL
AND employees_laid_off IS NOT NULL
ORDER BY layoff_date;

-- Query 12: Rank companies by layoffs within each industry
SELECT industry_name, company_name, total_laid_off,
       RANK() OVER (PARTITION BY industry_name 
                    ORDER BY total_laid_off DESC) AS rank_in_industry
FROM (
    SELECT i.industry_name,
           c.company_name,
           SUM(e.employees_laid_off) AS total_laid_off
    FROM layoff_events e
    JOIN companies c ON e.company_id = c.company_id
    JOIN industries i ON c.industry_id = i.industry_id
    WHERE e.employees_laid_off IS NOT NULL
    GROUP BY i.industry_name, c.company_name
) ranked
ORDER BY industry_name, rank_in_industry;

-- Query 13: Countries with highest avg percentage laid off
SELECT l.country,
       ROUND(AVG(e.percentage_laid_off) * 100, 2) AS avg_percentage,
       SUM(e.employees_laid_off) AS total_laid_off
FROM layoff_events e
JOIN companies c ON e.company_id = c.company_id
JOIN locations l ON c.location_id = l.location_id
WHERE e.percentage_laid_off IS NOT NULL
GROUP BY l.country
ORDER BY avg_percentage DESC
LIMIT 15;

-- Query 14: Worst single day of layoffs
SELECT layoff_date,
       SUM(employees_laid_off) AS total_laid_off,
       COUNT(*) AS companies_affected
FROM layoff_events
WHERE employees_laid_off IS NOT NULL
AND layoff_date IS NOT NULL
GROUP BY layoff_date
ORDER BY total_laid_off DESC
LIMIT 10;

-- Query 15: Companies with most funding that still laid off
SELECT c.company_name,
       e.funds_raised_millions,
       SUM(e.employees_laid_off) AS total_laid_off,
       e.stage
FROM layoff_events e
JOIN companies c ON e.company_id = c.company_id
WHERE e.funds_raised_millions IS NOT NULL
AND e.employees_laid_off IS NOT NULL
GROUP BY c.company_name, e.funds_raised_millions, e.stage
ORDER BY e.funds_raised_millions DESC
LIMIT 10;

-- ------------------------------------------------
-- VIEWS (Reusable Queries)
-- ------------------------------------------------

-- View 1: Company layoff summary
CREATE VIEW company_layoff_summary AS
SELECT c.company_name,
       i.industry_name,
       l.country,
       SUM(e.employees_laid_off) AS total_laid_off,
       ROUND(AVG(e.percentage_laid_off) * 100, 2) AS avg_percentage,
       COUNT(*) AS layoff_rounds
FROM layoff_events e
JOIN companies c ON e.company_id = c.company_id
JOIN industries i ON c.industry_id = i.industry_id
JOIN locations l ON c.location_id = l.location_id
GROUP BY c.company_name, i.industry_name, l.country;

-- View 2: Yearly industry trends
CREATE VIEW yearly_industry_trends AS
SELECT YEAR(e.layoff_date) AS year,
       i.industry_name,
       SUM(e.employees_laid_off) AS total_laid_off,
       COUNT(*) AS total_events
FROM layoff_events e
JOIN companies c ON e.company_id = c.company_id
JOIN industries i ON c.industry_id = i.industry_id
WHERE e.layoff_date IS NOT NULL
GROUP BY YEAR(e.layoff_date), i.industry_name;