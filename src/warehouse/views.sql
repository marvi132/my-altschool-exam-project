# vw_payment_success
SELECT
  COUNTIF(LOWER(payment_status) = 'success') AS successful_payments,
  COUNT(*) AS total_payments,
  ROUND(
    COUNTIF(LOWER(payment_status)='success')/COUNT(*)*100,
    2
    ) AS success_rate_percent
FROM commercepulse.payments


# vw_kpi_summarry
SELECT
  -- Orders
  (SELECT COUNT(*) FROM commercepulse.orders) AS total_orders,

  -- Payments
  (SELECT COUNT(*) FROM commercepulse.payments) AS total_payments,

  -- Successful Payments
  (SELECT COUNT(*) 
   FROM commercepulse.payments 
   WHERE LOWER(payment_status) = 'success') AS successful_payments,

  -- Failed Payments
  (SELECT COUNT(*) 
   FROM commercepulse.payments 
   WHERE LOWER(payment_status) != 'success') AS failed_payments,

  -- Revenue
  (SELECT SUM(amountpaid)
   FROM commercepulse.payments
   WHERE LOWER(payment_status) = 'success') AS total_revenue,

  -- Average Successful Payment
  (SELECT AVG(amountpaid)
   FROM commercepulse.payments
   WHERE LOWER(payment_status) = 'success') AS avg_successful_payment,

  -- Payment Success Rate
  ROUND(
    (SELECT COUNT(*) 
     FROM commercepulse.payments 
     WHERE LOWER(payment_status) = 'success')
    /
    (SELECT COUNT(*) FROM commercepulse.payments)
    * 100,
    2
  ) AS payment_success_rate_percent



  # monthly_revenue
  SELECT
  FORMAT_DATE('%Y-%m', DATE(paid_at)) AS revenue_month,
  COUNT(order_id) AS total_orders,
  SUM(amountpaid) AS total_revenue,
  AVG(amountpaid) AS avg_order_value
FROM commercepulse.payments
WHERE LOWER(payment_status) = 'success'
GROUP BY revenue_month
ORDER BY revenue_month


# vw_monthlyrevenue_growth
WITH monthly AS (
  SELECT
    FORMAT_DATE('%Y-%m', DATE(paid_at)) AS revenue_month,
    SUM(amountpaid) AS total_revenue
  FROM commercepulse.payments
  WHERE LOWER(payment_status) = 'success'
  GROUP BY revenue_month
)

SELECT
  revenue_month,
  total_revenue,
  LAG(total_revenue) OVER (ORDER BY revenue_month) AS previous_month_revenue,

  ROUND(
    (total_revenue - LAG(total_revenue) OVER (ORDER BY revenue_month))
    / LAG(total_revenue) OVER (ORDER BY revenue_month)
    * 100,
    2
  ) AS mom_growth_percent

FROM monthly
ORDER BY revenue_month


# top_channels
WITH channel_revenue AS (
  SELECT
    channel,
    SUM(amountpaid) AS total_revenue,
    COUNT(*) AS total_transactions
  FROM commercepulse.payments
  WHERE LOWER(payment_status) = 'success'
  GROUP BY channel
)

SELECT
  channel,
  total_revenue,
  total_transactions,
  RANK() OVER (ORDER BY total_revenue DESC) AS revenue_rank
FROM channel_revenue
ORDER BY revenue_rank



# executives_dashboard
WITH revenue_data AS (
  SELECT
    SUM(CASE WHEN LOWER(payment_status) = 'success' THEN amountpaid ELSE 0 END) AS total_revenue,
    COUNT(*) AS total_payments,
    COUNTIF(LOWER(payment_status) = 'success') AS successful_payments
  FROM commercepulse.payments
),

refund_data AS (
  SELECT
    COUNT(*) AS total_refunds
  FROM commercepulse.refunds
),

top_channel AS (
  SELECT
    channel,
    SUM(amountpaid) AS channel_revenue
  FROM commercepulse.payments
  WHERE LOWER(payment_status) = "success"
  GROUP BY channel
  ORDER BY channel_revenue DESC
  LIMIT 1
)

SELECT
  r.total_revenue,
  r.total_payments,
  r.successful_payments,
  ROUND(r.successful_payments / r.total_payments * 100,2) AS payment_success_rate_percent, 
  f.total_refunds,
  t.channel AS top_channel,
  t.channel_revenue AS top_channel_revenue
FROM revenue_data r
CROSS JOIN refund_data f
CROSS JOIN top_channel t


# vw_refund_metrics
SELECT
  (SELECT SUM(amount) FROM commercepulse.refunds) AS total_refund_amount,
  (SELECT SUM(amount) FROM commercepulse.orders) AS total_order_amount,
  SAFE_DIVIDE(
    (SELECT SUM(amount) FROM commercepulse.refunds),
    (SELECT SUM(amount) FROM commercepulse.orders)
  ) AS refund_rate