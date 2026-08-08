from datetime import datetime, date
from werkzeug.security import generate_password_hash, check_password_hash
from extensions import db

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
trek_status = (status_pending_trek, status_approved_trek, status_open_trek, status_closed_trek, status_completed_trek)
difficulty = ("Easy", "Moderate", "Hard")
status_booked_booking = "Booked"
status_cancelled_booking = "Cancelled"
status_completed_booking = "Completed"
status_pending_payment = "Pending"
status_paid_payment = "Paid"
status_NA_payment = "Not Applicable"

#User Table 
class User(db.Model):
    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True)
    fullName = db.Column(db.String(120), nullable=False)
    email = db.Column(db.String(150), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(255), nullable=False)
    phone = db.Column(db.String(20), nullable=True)
    role = db.Column(db.String(20), nullable=False, default=roleOfTrekker)
    status = db.Column(db.String(20), nullable=False, default=status_active_trekker)
    createdAt = db.Column(db.DateTime, default=datetime.utcnow)

    treksAssigned = db.relationship("Trek", back_populates="staff", foreign_keys="Trek.staffId")
    bookings = db.relationship("Booking", back_populates="trekker", foreign_keys="Booking.userId", cascade="all, delete-orphan")
    exportJobs = db.relationship("ExportJob", back_populates="user", cascade="all, delete-orphan")

    def set_password(self, raw_password: str) -> None:
        self.password_hash = generate_password_hash(raw_password)

    def check_password(self, raw_password: str) -> bool:
        return check_password_hash(self.password_hash, raw_password)

    def is_blacklisted(self) -> bool:
        return self.status in (status_blacklisted_staff, status_blacklisted_trekker)

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

#Trek Table
class Trek(db.Model):
    __tablename__ = "treks"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(150), nullable=False)
    location = db.Column(db.String(150), nullable=False)
    difficulty = db.Column(db.String(20), nullable=False, default="Easy")
    durationOfDays = db.Column(db.Integer, nullable=False, default=1)
    totalSlots = db.Column(db.Integer, nullable=False, default=10)
    slotsAvailable = db.Column(db.Integer, nullable=False, default=10)
    staffId = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=True)
    status = db.Column(db.String(20), nullable=False, default=status_pending_trek)
    startDate = db.Column(db.Date, nullable=False, default=date.today)
    endDate = db.Column(db.Date, nullable=False, default=date.today)
    description = db.Column(db.Text, nullable=True)
    price = db.Column(db.Float, nullable=False, default=0.0)
    createdAt = db.Column(db.DateTime, default=datetime.utcnow)

    staff = db.relationship("User", back_populates="treksAssigned", foreign_keys=[staffId])
    bookings = db.relationship("Booking", back_populates="trek", cascade="all, delete-orphan")

    @property
    def active_booking_count(self):
        return sum(1 for b in self.bookings if b.status in (status_booked_booking, status_completed_booking))

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
            "price": self.price,
            "staffId": self.staffId,
            "staff_name": self.staff.fullName if self.staff else None,
        }
        if for_role in ("admin", "staff"):
            data["active_bookings"] = self.active_booking_count
        return data

#Bookings Table
class Booking(db.Model):
    __tablename__ = "bookings"

    id = db.Column(db.Integer, primary_key=True)
    userId = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    trekId = db.Column(db.Integer, db.ForeignKey("treks.id"), nullable=False)
    bookingDate = db.Column(db.DateTime, default=datetime.utcnow)
    status = db.Column(db.String(20), nullable=False, default=status_booked_booking)
    paymentStatus = db.Column(db.String(20), nullable=False, default=status_NA_payment)

    trekker = db.relationship("User", back_populates="bookings", foreign_keys=[userId])
    trek = db.relationship("Trek", back_populates="bookings", foreign_keys=[trekId])

    __table_args__ = (
        db.Index("ix_booking_user_trek", "userId", "trekId"),
    )

    def to_dict(self):
        return {
            "id": self.id,
            "userId": self.userId,
            "trekId": self.trekId,
            "trek_name": self.trek.name if self.trek else None,
            "location": self.trek.location if self.trek else None,
            "bookingDate": self.bookingDate.isoformat() if self.bookingDate else None,
            "status": self.status,
            "paymentStatus": self.paymentStatus,
            "startDate": self.trek.startDate.isoformat() if self.trek and self.trek.startDate else None,
            "endDate": self.trek.endDate.isoformat() if self.trek and self.trek.endDate else None,
        }

#Export Table
class ExportJob(db.Model):
    __tablename__ = "exportJobs"

    id = db.Column(db.Integer, primary_key=True)
    userId = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    celeryTaskId = db.Column(db.String(64), nullable=True)
    status = db.Column(db.String(20), nullable=False, default="Pending")  # Pending/Running/Done/Failed
    filePath = db.Column(db.String(255), nullable=True)
    createdAt = db.Column(db.DateTime, default=datetime.utcnow)
    completedAt = db.Column(db.DateTime, nullable=True)

    user = db.relationship("User", back_populates="exportJobs")

    def to_dict(self):
        return {
            "id": self.id,
            "status": self.status,
            "createdAt": self.createdAt.isoformat() if self.createdAt else None,
            "completedAt": self.completedAt.isoformat() if self.completedAt else None,
            "download_url": f"/api/user/exports/{self.id}/download" if self.status == "Done" else None,
        }
