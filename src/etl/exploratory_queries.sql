-- row_counts
SELECT 'companies' AS table_name, COUNT(*) AS rows FROM companies
        UNION ALL SELECT 'profitandloss', COUNT(*) FROM profitandloss
        UNION ALL SELECT 'balancesheet', COUNT(*) FROM balancesheet
        UNION ALL SELECT 'cashflow', COUNT(*) FROM cashflow
        UNION ALL SELECT 'stock_prices', COUNT(*) FROM stock_prices;

-- company_count
SELECT COUNT(*) AS company_count
        FROM companies;

-- year_coverage
SELECT
            company_id,
            MIN(year) AS first_year,
            MAX(year) AS last_year,
            COUNT(DISTINCT year) AS years_available
        FROM profitandloss
        GROUP BY company_id
        ORDER BY years_available;

-- companies_fewer_than_5_years
SELECT
            company_id,
            COUNT(DISTINCT year) AS years_available
        FROM profitandloss
        GROUP BY company_id
        HAVING years_available < 5;

-- duplicate_company_year
SELECT
            company_id,
            year,
            COUNT(*) AS occurrences
        FROM profitandloss
        GROUP BY company_id, year
        HAVING occurrences > 1;

-- orphan_profitandloss_company_ids
SELECT p.company_id
        FROM profitandloss p
        LEFT JOIN companies c ON p.company_id = c.id
        WHERE c.id IS NULL;

-- profitandloss_null_counts
SELECT
            SUM(CASE WHEN sales IS NULL THEN 1 ELSE 0 END) AS null_sales,
            SUM(CASE WHEN net_profit IS NULL THEN 1 ELSE 0 END) AS null_net_profit,
            SUM(CASE WHEN eps IS NULL THEN 1 ELSE 0 END) AS null_eps
        FROM profitandloss;

-- sector_distribution
SELECT
            broad_sector,
            COUNT(*) AS company_count
        FROM sectors
        GROUP BY broad_sector
        ORDER BY company_count DESC;

-- balance_sheet_imbalance
SELECT
            company_id,
            year,
            total_assets,
            total_liabilities,
            ROUND(ABS(total_assets - total_liabilities) * 100.0 / total_assets, 2) AS diff_pct
        FROM balancesheet
        WHERE ABS(total_assets - total_liabilities) * 1.0 / total_assets >= 0.01
        ORDER BY diff_pct DESC;

-- negative_or_zero_sales
SELECT
            company_id,
            year,
            sales
        FROM profitandloss
        WHERE sales <= 0;

