from src.database import get_db_session
from src.services.admin_service import AdminService
from datetime import date

def fix_room():
    with get_db_session() as session:
        pass
        # admin = AdminService(session)
        # print(admin.update_room_date(405, date(2026, 4, 7)))

# if __name__ == "__main__":
#     fix_room()
