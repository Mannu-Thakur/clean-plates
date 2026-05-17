"""
Seed script — populate mock devices, students, and 30 days of waste entries to make analytics beautiful!
"""
from __future__ import annotations

import asyncio
import uuid
import random
from datetime import datetime, date, timedelta

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.core.config import settings
from app.models.user import UserModel
from app.models.device import DeviceModel
from app.models.student import StudentModel, StudentMappingModel
from app.models.waste import WasteEntryModel
from app.models.warning import WarningModel, PenaltyModel
from app.models.audit import AuditEventModel

async def seed_mock_analytics():
    engine = create_async_engine(
        settings.DATABASE_URL,
        connect_args={"check_same_thread": False, "timeout": 15},
    )
    session_factory = async_sessionmaker(bind=engine, class_=AsyncSession, expire_on_commit=False)

    async with session_factory() as session:
        # 1. Get the admin user
        admin_res = await session.execute(select(UserModel).where(UserModel.email == "admin@cleanplates.dev"))
        admin = admin_res.scalar_one_or_none()
        if not admin:
            print("Please run scripts/seed_admin.py first!")
            return
        admin_id = admin.id

        # 2. Check if mock device exists
        dev_res = await session.execute(select(DeviceModel).where(DeviceModel.device_serial == "pi-main"))
        device = dev_res.scalar_one_or_none()
        if not device:
            device = DeviceModel(
                id=str(uuid.uuid4()),
                device_serial="pi-main",
                edge_node_name="Pi Main Entrance",
                institution_name="CleanPlates Institution",
                institution_code="CP",
                campus_name="Main Campus",
                mess_name="Central Mess",
                mess_id="MESS-01",
                status="online",
                is_deleted=False
            )
            session.add(device)
            await session.flush()
            print("[OK] Seeded Device pi-main")
        else:
            print("[SKIP] Device pi-main already exists")

        # 3. Create students
        student_data = [
            {"card": "card-101", "name": "Aarav Sharma", "branch": "CSE", "year": 3, "hostel": "Ramanujan", "avg_waste": 120.0, "status": "orange", "warning_count": 2, "penalty_count": 0},
            {"card": "card-102", "name": "Aditi Patel", "branch": "ECE", "year": 2, "hostel": "Aryabhatta", "avg_waste": 60.0, "status": "green", "warning_count": 0, "penalty_count": 0},
            {"card": "card-103", "name": "Kabir Singh", "branch": "ME", "year": 4, "hostel": "Bhabha", "avg_waste": 180.0, "status": "red", "warning_count": 5, "penalty_count": 1},
            {"card": "card-104", "name": "Diya Iyer", "branch": "CSE", "year": 1, "hostel": "Sarabhai", "avg_waste": 40.0, "status": "green", "warning_count": 0, "penalty_count": 0},
            {"card": "card-105", "name": "Vivaan Reddy", "branch": "CE", "year": 3, "hostel": "Bhabha", "avg_waste": 240.0, "status": "red", "warning_count": 6, "penalty_count": 2},
        ]

        students_map = {}
        for s in student_data:
            s_res = await session.execute(select(StudentModel).where(StudentModel.device_id == s["card"]))
            student = s_res.scalar_one_or_none()
            if not student:
                student = StudentModel(
                    id=str(uuid.uuid4()),
                    device_id=s["card"],
                    status=s["status"],
                    is_status_manual=False,
                    sustainability_score=max(10.0, 100.0 - (s["avg_waste"] / 3.0)),
                    warning_count=s["warning_count"],
                    penalty_count=s["penalty_count"],
                    total_waste_grams=s["avg_waste"] * 90.0,
                    avg_waste_grams=s["avg_waste"],
                    is_active=True
                )
                session.add(student)
                await session.flush()

                mapping = StudentMappingModel(
                    id=str(uuid.uuid4()),
                    student_id=student.id,
                    device_id=s["card"],
                    name=s["name"],
                    roll_number=f"ROLL-{s['card'].split('-')[1]}",
                    branch=s["branch"],
                    year=s["year"],
                    hostel=s["hostel"],
                    room_number=f"ROOM-{random.randint(101, 309)}",
                    email=f"{s['name'].split()[0].lower()}@cleanplates.dev",
                    mapped_by=admin_id
                )
                session.add(mapping)
                await session.flush()
                print(f"[OK] Seeded student: {s['name']}")
            else:
                print(f"[SKIP] Student {s['name']} already exists")
            students_map[s["card"]] = student

        # 4. Generate 30 days of waste entries
        w_res = await session.execute(select(WasteEntryModel).limit(1))
        existing_w = w_res.scalar_one_or_none()
        if existing_w:
            print("[SKIP] Waste entries already seeded.")
        else:
            print("Seeding waste entries for the last 30 days...")
            today = date.today()
            food_by_meal = {
                "breakfast": [
                    {"name": "idli", "grams": 40}, {"name": "poha", "grams": 60},
                    {"name": "sambar", "grams": 50}, {"name": "chutney", "grams": 20},
                    {"name": "bread", "grams": 30}
                ],
                "lunch": [
                    {"name": "rice", "grams": 100}, {"name": "dal", "grams": 60},
                    {"name": "sabzi", "grams": 80}, {"name": "roti", "grams": 40},
                    {"name": "curd", "grams": 30}
                ],
                "dinner": [
                    {"name": "roti", "grams": 50}, {"name": "paneer", "grams": 90},
                    {"name": "dal fry", "grams": 60}, {"name": "jeera rice", "grams": 80},
                    {"name": "salad", "grams": 20}
                ]
            }

            entries_added = 0
            for i in range(30):
                session_date = today - timedelta(days=i)
                for student_idx, (card, student) in enumerate(students_map.items()):
                    s_info = next(item for item in student_data if item["card"] == card)
                    base_avg = s_info["avg_waste"]

                    for meal in ["breakfast", "lunch", "dinner"]:
                        meal_factor = 0.6 if meal == "breakfast" else (1.1 if meal == "lunch" else 1.3)
                        weight = base_avg * meal_factor * random.uniform(0.6, 1.4)
                        weight = max(5.0, round(weight, 1))

                        available_foods = food_by_meal[meal]
                        sampled = random.sample(available_foods, k=min(len(available_foods), random.randint(2, 3)))
                        total_sample_grams = sum(f["grams"] for f in sampled)
                        food_items = []
                        for f in sampled:
                            pct = f["grams"] / total_sample_grams
                            food_items.append({"name": f["name"], "grams": round(weight * pct, 1)})

                        hour = 8 if meal == "breakfast" else (13 if meal == "lunch" else 20)
                        # Guarantee no timestamp overlap on the same device by partitioning the minutes
                        minute = student_idx * 10 + random.randint(0, 9)
                        timestamp = datetime.combine(session_date, datetime.min.time()).replace(hour=hour, minute=minute)

                        severity = "normal"
                        if weight > 200.0:
                            severity = "high"
                        elif weight > 100.0:
                            severity = "warning"

                        entry = WasteEntryModel(
                            id=str(uuid.uuid4()),
                            student_id=student.id,
                            device_id=device.id,
                            weight_grams=weight,
                            meal_type=meal,
                            food_items=food_items,
                            confidence_score=round(random.uniform(0.85, 0.99), 2),
                            plate_image_path=f"/uploads/plates/mock-{uuid.uuid4().hex[:8]}.jpg",
                            session_date=session_date,
                            timestamp=timestamp,
                            severity=severity,
                            rule_evaluated=True,
                            source="ml"
                        )
                        session.add(entry)
                        entries_added += 1

            print(f"[OK] Seeded {entries_added} waste entries over 30 days.")

        # 5. Create some warning and penalty records for Red/Orange students
        warn_res = await session.execute(select(WarningModel).limit(1))
        existing_warn = warn_res.scalar_one_or_none()
        if existing_warn:
            print("[SKIP] Warnings and penalties already seeded.")
        else:
            kabir = students_map["card-103"]
            vivaan = students_map["card-105"]
            aarav = students_map["card-101"]

            for j in range(3):
                w = WarningModel(
                    id=str(uuid.uuid4()),
                    student_id=kabir.id,
                    level="level_1" if j < 2 else "level_2",
                    reason="Excessive food waste in consecutive meals (over 200g)",
                    status="active",
                    created_at=datetime.utcnow() - timedelta(days=j*3),
                    updated_at=datetime.utcnow() - timedelta(days=j*3)
                )
                session.add(w)

            p = PenaltyModel(
                id=str(uuid.uuid4()),
                student_id=kabir.id,
                points=1,
                reason="Repeated high food waste levels leading to automatic penalty",
                status="active",
                created_at=datetime.utcnow() - timedelta(days=1)
            )
            session.add(p)

            for j in range(4):
                w = WarningModel(
                    id=str(uuid.uuid4()),
                    student_id=vivaan.id,
                    level="level_1" if j < 2 else ("level_2" if j < 3 else "level_3"),
                    reason="High food waste alert - student repeatedly discarding > 250g",
                    status="active",
                    created_at=datetime.utcnow() - timedelta(days=j*2),
                    updated_at=datetime.utcnow() - timedelta(days=j*2)
                )
                session.add(w)

            p1 = PenaltyModel(
                id=str(uuid.uuid4()),
                student_id=vivaan.id,
                points=2,
                reason="Multiple system warnings ignored. Sustainability violation penalty.",
                status="active",
                created_at=datetime.utcnow() - timedelta(days=2)
            )
            session.add(p1)

            w_aarav = WarningModel(
                id=str(uuid.uuid4()),
                student_id=aarav.id,
                level="level_1",
                reason="Food waste alert - meal wastage exceeded warning threshold (100g)",
                status="active",
                created_at=datetime.utcnow() - timedelta(days=5),
                updated_at=datetime.utcnow() - timedelta(days=5)
            )
            session.add(w_aarav)

            print("[OK] Seeded 8 Warnings and 3 Penalties for Red/Orange students.")

        # 6. Seed some Audit Events
        audit_count_res = await session.execute(select(AuditEventModel).limit(1))
        if audit_count_res.scalar_one_or_none():
            print("[SKIP] Audit events already populated.")
        else:
            aarav = students_map["card-101"]
            session.add_all([
                AuditEventModel(
                    id=str(uuid.uuid4()),
                    event_type="auth.login",
                    action="login",
                    resource_type="user",
                    resource_id=admin_id,
                    user_id=admin_id,
                    user_name="System Admin",
                    user_role="super_admin",
                    summary="User admin@cleanplates.dev logged in successfully",
                    created_at=datetime.utcnow() - timedelta(minutes=30)
                ),
                AuditEventModel(
                    id=str(uuid.uuid4()),
                    event_type="device.registered",
                    action="create",
                    resource_type="device",
                    resource_id="pi-main",
                    user_id=admin_id,
                    user_name="System Admin",
                    user_role="super_admin",
                    summary="Registered new edge node device: pi-main",
                    created_at=datetime.utcnow() - timedelta(days=29)
                ),
                AuditEventModel(
                    id=str(uuid.uuid4()),
                    event_type="student.mapped",
                    action="create",
                    resource_type="student",
                    resource_id=aarav.id,
                    user_id=admin_id,
                    user_name="System Admin",
                    user_role="super_admin",
                    summary="Mapped card identity card-101 to Aarav Sharma",
                    created_at=datetime.utcnow() - timedelta(days=28)
                )
            ])
            print("[OK] Seeded rich audit logs.")

        await session.commit()

    await engine.dispose()
    print("\n[DONE] Mock analytics seeding complete.")

if __name__ == "__main__":
    asyncio.run(seed_mock_analytics())
