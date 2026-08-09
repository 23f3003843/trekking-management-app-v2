from datetime import datetime, date
from werkzeug.security import generate_password_hash, check_password_hash
from extensions import database

roleOfAdmin = "admin"
roleOfStaff = "staff"
roleOfTrekker = "trekker"
roles = (roleOfAdmin, roleOfStaff, roleOfTrekker)
status_pending_staff = "Pending"
status_approved_staff = "Approved"
status_blacklisted_staff = "Blacklisted"
status_active_trekker = "Active"
status_blacklisted_trekker = "Blacklisted"
status_pending_trek = "Pending"
status_approved_trek = "Approved"
status_open_trek = "Open"
status_closed_trek = "Closed"
status_completed_trek = "Completed"
trek_status = (status_pending_trek, status_approved_trek, status_open_trek, status_closed_trek,status_completed_trek)

difficulty = ("Easy", "Moderate", "Hard")

status_booked_booking = "Booked"
status_cancelled_booking = "Cancelled"
status_completed_booking = "Completed"

# User Table
class User(database.Model):
    __tablename__ = "users"

    id = database.Column(database.Integer, primary_key=True)
    fullName = database.Column(database.String(120), nullable=False)
    email = database.Column(database.String(150), unique=True, nullable=False, index=True)
    password_hash = database.Column(database.String(255), nullable=False)
    phone = database.Column(database.String(20), nullable=True)
    role = database.Column(database.String(20), nullable=False, default=roleOfTrekker)
    status = database.Column(database.String(20), nullable=False, default=status_active_trekker)
    createdAt = database.Column(database.DateTime, default=datetime.utcnow)

    treksAssigned = database.relationship("Trek", back_populates="staff", foreign_keys="Trek.staffId")
    bookings = database.relationship("Booking", back_populates="trekker", foreign_keys="Booking.userId", cascade="all, delete-orphan",)
    exportJobs = database.relationship("ExportJob", back_populates="user", cascade="all, delete-orphan",)

    def set_password(self, raw_password: str) -> None:
        self.password_hash = generate_password_hash(raw_password)

    def check_password(self, raw_password: str) -> bool:
        return check_password_hash(self.password_hash, raw_password)

    def is_blacklisted(self) -> bool:
        return self.status in (
            status_blacklisted_staff,
            status_blacklisted_trekker,
        )

    def to_dict(self, include_email=True):
        data = {
            "id": self.id,
            "fullName": self.fullName,
            "role": self.role,
            "status": self.status,
            "phone": self.phone,
            "createdAt": self.createdAt.isoformat() if self.createdAt else None,
        }

        if include_email:
            data["email"] = self.email

        return data

# Trek Table
class Trek(database.Model):
    __tablename__ = "treks"

    id = database.Column(database.Integer, primary_key=True)
    name = database.Column(database.String(150), nullable=False)
    location = database.Column(database.String(150), nullable=False)
    difficulty = database.Column(database.String(20), nullable=False, default="Easy")
    durationOfDays = database.Column(database.Integer, nullable=False, default=1)
    totalSlots = database.Column(database.Integer, nullable=False, default=10)
    slotsAvailable = database.Column(database.Integer, nullable=False, default=10)
    staffId = database.Column(database.Integer, database.ForeignKey("users.id"), nullable=True)
    status = database.Column(database.String(20), nullable=False, default=status_pending_trek)
    startDate = database.Column(database.Date, nullable=False, default=date.today)
    endDate = database.Column(database.Date, nullable=False, default=date.today)
    description = database.Column(database.Text, nullable=True)
    createdAt = database.Column(database.DateTime, default=datetime.utcnow)

    staff = database.relationship(
        "User",
        back_populates="treksAssigned",
        foreign_keys=[staffId],
    )
    bookings = database.relationship(
        "Booking",
        back_populates="trek",
        cascade="all, delete-orphan",
    )

    @property
    def active_booking_count(self):
        return sum(1 for b in self.bookings if b.status in (status_booked_booking,status_completed_booking))

    def to_dict(self, for_role="trekker"):
        data = {
            "id": self.id,
            "name": self.name,
            "location": self.location,
            "difficulty": self.difficulty,
            "durationOfDays": self.durationOfDays,
            "totalSlots": self.totalSlots,
            "slotsAvailable": self.slotsAvailable,
            "status": self.status,
            "startDate": self.startDate.isoformat() if self.startDate else None,
            "endDate": self.endDate.isoformat() if self.endDate else None,
            "description": self.description,
            "staffId": self.staffId,
            "staff_name": self.staff.fullName if self.staff else None,
        }

        if for_role in ("admin", "staff"):
            data["active_bookings"] = self.active_booking_count

        return data

# Bookings Table
class Booking(database.Model):
    __tablename__ = "bookings"

    id = database.Column(database.Integer, primary_key=True)
    userId = database.Column(database.Integer, database.ForeignKey("users.id"), nullable=False)
    trekId = database.Column(database.Integer, database.ForeignKey("treks.id"), nullable=False)
    bookingDate = database.Column(database.DateTime, default=datetime.utcnow)
    status = database.Column(database.String(20), nullable=False, default=status_booked_booking)

    trekker = database.relationship("User", back_populates="bookings", foreign_keys=[userId])
    trek = database.relationship("Trek", back_populates="bookings", foreign_keys=[trekId])

    __table_args__ = (database.Index("ix_booking_user_trek", "userId", "trekId"),)

    def to_dict(self):
        return {
            "id": self.id,
            "userId": self.userId,
            "trekId": self.trekId,
            "trek_name": self.trek.name if self.trek else None,
            "location": self.trek.location if self.trek else None,
            "bookingDate": (
                self.bookingDate.isoformat()
                if self.bookingDate
                else None
            ),
            "status": self.status,
            "startDate": (
                self.trek.startDate.isoformat()
                if self.trek and self.trek.startDate
                else None
            ),
            "endDate": (
                self.trek.endDate.isoformat()
                if self.trek and self.trek.endDate
                else None
            ),
        }


# Export Table
class ExportJob(database.Model):
    __tablename__ = "exportJobs"

    id = database.Column(database.Integer, primary_key=True)
    userId = database.Column(database.Integer, database.ForeignKey("users.id"), nullable=False)
    celeryTaskId = database.Column(database.String(64), nullable=True)
    status = database.Column(database.String(20), nullable=False, default="Pending")  # Pending/Running/Done/Failed
    filePath = database.Column(database.String(255), nullable=True)
    createdAt = database.Column(database.DateTime, default=datetime.utcnow)
    completedAt = database.Column(database.DateTime, nullable=True)

    user = database.relationship("User", back_populates="exportJobs")

    def to_dict(self):
        return {
            "id": self.id,
            "status": self.status,
            "createdAt": (
                self.createdAt.isoformat()
                if self.createdAt
                else None
            ),
            "completedAt": (
                self.completedAt.isoformat()
                if self.completedAt
                else None
            ),
            "download_url": (
                f"/api/user/exports/{self.id}/download"
                if self.status == "Done"
                else None
            ),
        }