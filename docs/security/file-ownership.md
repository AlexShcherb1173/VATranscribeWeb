# File Ownership

Every file/media/job/transcript/export must be scoped by user_id.

Rule:
Do not fetch by id only. Always fetch by id plus current_user.id.
