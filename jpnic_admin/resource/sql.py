sql_get_latest = """
SELECT t1.id                                  AS ID,
       t1.jpnic_id                            AS JPNIC_ID,
       t1.created_at                          AS created_at,
       t1.last_checked_at                     AS last_checked_at,
       t1.type                                AS type,
       t1.division                            AS division,
       t1.ip_address                          AS ip_address,
       t1.network_name                        AS network_name,
       t1.abuse                               AS abuse,
       t1.org                                 AS org,
       t1.post_code                           AS postcode,
       t1.address                             AS address,
       t1.address_en                          AS address_en,
       t1.admin_handle                        AS admin_handle,
       tb_admin_handle.name                   AS admin_name,
       tb_admin_handle.email                  AS admin_email,
       GROUP_CONCAT(tech_handle.jpnic_handle) AS tech_handle,
       GROUP_CONCAT(tech_handle.name)         AS tech_name,
       GROUP_CONCAT(tech_handle.email)        AS tech_email
FROM resource_addrlist AS t1
         JOIN (SELECT MAX(id) AS id, admin_handle
               FROM resource_addrlist
               WHERE resource_addrlist.last_checked_at = %s
                 AND resource_addrlist.jpnic_id = %s
                 AND resource_addrlist.network_name like %s
                 AND (resource_addrlist.address like %s OR resource_addrlist.address_en like %s)
               GROUP BY ip_address, admin_handle, assign_date, type, division
               # HAVING MAX(id)
               ORDER BY ip_address
               LIMIT %s OFFSET %s) AS t2 ON t1.id = t2.id
         INNER JOIN resource_jpnichandle AS tb_admin_handle ON t2.admin_handle = tb_admin_handle.jpnic_handle
         INNER JOIN resource_addrlisttechhandle ON t2.id = resource_addrlisttechhandle.addr_list_id
         INNER JOIN resource_jpnichandle AS tech_handle
                    ON resource_addrlisttechhandle.jpnic_handle = tech_handle.jpnic_handle
GROUP BY id, ip_address, admin_name, admin_email
ORDER BY ip_address
"""

sqlDateSelect = """
SELECT t1.id                                  AS ID,
       t1.jpnic_id                            AS JPNIC_ID,
       t1.created_at                          AS created_at,
       t1.last_checked_at                     AS last_checked_at,
       t1.type                                AS type,
       t1.division                            AS division,
       t1.ip_address                          AS ip_address,
       t1.network_name                        AS network_name,
       t1.abuse                               AS abuse,
       t1.org                                 AS org,
       t1.post_code                           AS postcode,
       t1.address                             AS address,
       t1.address_en                          AS address_en,
       t1.admin_handle                        AS admin_handle,
       tb_admin_handle.name                   AS admin_name,
       tb_admin_handle.email                  AS admin_email,
       GROUP_CONCAT(tech_handle.jpnic_handle) AS tech_handle,
       GROUP_CONCAT(tech_handle.name)         AS tech_name,
       GROUP_CONCAT(tech_handle.email)        AS tech_email
FROM resource_addrlist AS t1
         JOIN (SELECT MAX(id) AS id, admin_handle
               FROM resource_addrlist
               WHERE NOT (resource_addrlist.last_checked_at <= %s OR %s <= resource_addrlist.created_at)
                 AND resource_addrlist.jpnic_id = %s
                 AND resource_addrlist.network_name like %s
                 AND (resource_addrlist.address like %s OR resource_addrlist.address_en like %s)
               GROUP BY ip_address, admin_handle, assign_date, type, division
               # HAVING MAX(id)
               ORDER BY ip_address
               LIMIT %s OFFSET %s) AS t2 ON t1.id = t2.id
         INNER JOIN resource_jpnichandle AS tb_admin_handle ON t2.admin_handle = tb_admin_handle.jpnic_handle
         INNER JOIN resource_addrlisttechhandle ON t2.id = resource_addrlisttechhandle.addr_list_id
         INNER JOIN resource_jpnichandle AS tech_handle
                    ON resource_addrlisttechhandle.jpnic_handle = tech_handle.jpnic_handle
GROUP BY id, ip_address, admin_name, admin_email
ORDER BY ip_address
"""

sqlDateSelectCount = """
SELECT resource_addrlist.ip_address   AS ip_address,
       resource_addrlist.division     AS division
FROM resource_addrlist 
WHERE NOT (resource_addrlist.last_checked_at <= %s OR %s <= resource_addrlist.created_at)
 AND resource_addrlist.jpnic_id = %s
 AND resource_addrlist.network_name like %s
 AND (resource_addrlist.address like %s OR resource_addrlist.address_en like %s)
GROUP BY  ip_address, division
"""

sqlAddrListDateFilter = """
WITH rs_addrlist AS (SELECT *
                     FROM resource_resourceaddresslist T1
                     WHERE T1.`jpnic_id` = %(id)s
                       AND NOT (T1.`last_checked_at` < %(start_time)s)
                       AND NOT (T1.`created_at` > %(end_time)s))
SELECT *
FROM rs_addrlist
WHERE NOT EXISTS(
        SELECT 1
        FROM rs_addrlist AS sub
        WHERE rs_addrlist.ip_address = sub.ip_address
          AND rs_addrlist.last_checked_at < sub.last_checked_at
    )
"""
