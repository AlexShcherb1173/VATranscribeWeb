# Billing Flow

Subscription flow:
pricing page -> checkout request -> payment provider -> provider webhook -> payment succeeded -> subscription active -> quotas synced -> user gets paid access

Rule:
Frontend redirect is not a source of truth. Payment provider webhook is the source of truth.
