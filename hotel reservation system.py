import json
import os
import uuid
from datetime import datetime


class Room:
    """Represents a hotel room with its category, pricing, and availability."""

    def __init__(self, room_number, category, price_per_night, is_available=True):
        self.room_number = room_number
        self.category = category  # Standard, Deluxe, Suite
        self.price_per_night = price_per_night
        self.is_available = is_available

    def to_dict(self):
        return {
            "room_number": self.room_number,
            "category": self.category,
            "price_per_night": self.price_per_night,
            "is_available": self.is_available,
        }

    @classmethod
    def from_dict(cls, data):
        return cls(
            data["room_number"],
            data["category"],
            data["price_per_night"],
            data["is_available"],
        )


class Reservation:
    """Represents a customer's booking record."""

    def __init__(
        self,
        booking_id,
        guest_name,
        guest_phone,
        room_number,
        category,
        nights,
        total_amount,
        payment_status,
        transaction_id,
        status="Confirmed",
    ):
        self.booking_id = booking_id
        self.guest_name = guest_name
        self.guest_phone = guest_phone
        self.room_number = room_number
        self.category = category
        self.nights = nights
        self.total_amount = total_amount
        self.payment_status = payment_status
        self.transaction_id = transaction_id
        self.status = status  # Confirmed, Cancelled
        self.booked_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    def to_dict(self):
        return self.__dict__

    @classmethod
    def from_dict(cls, data):
        res = cls(
            data["booking_id"],
            data["guest_name"],
            data["guest_phone"],
            data["room_number"],
            data["category"],
            data["nights"],
            data["total_amount"],
            data["payment_status"],
            data["transaction_id"],
            data["status"],
        )
        res.booked_at = data.get("booked_at", res.booked_at)
        return res


class PaymentGateway:
    """Simulates payment processing."""

    @staticmethod
    def process_payment(amount):
        print(f"\n--- Payment Gateway (Amount Due: ₹{amount:,.2f}) ---")
        print("1. UPI (GPay / PhonePe / Paytm)")
        print("2. Credit / Debit Card")
        print("3. Net Banking")
        choice = input("Select payment method (1-3): ").strip()

        methods = {"1": "UPI", "2": "Card", "3": "Net Banking"}
        if choice not in methods:
            print("Invalid payment method selected. Transaction aborted.")
            return False, None

        print(f"Processing ₹{amount:,.2f} via {methods[choice]}...")
        confirm = input("Confirm payment? (y/n): ").strip().lower()

        if confirm == "y":
            txn_id = f"TXN-{uuid.uuid4().hex[:8].upper()}"
            print(f"Payment Successful! Transaction ID: {txn_id}")
            return True, txn_id
        else:
            print("Payment declined by user.")
            return False, None


class HotelSystem:
    """Manages hotel operations, rooms, reservations, and File I/O."""

    def __init__(self, data_file="hotel_data.json"):
        self.data_file = data_file
        self.rooms = []
        self.reservations = []
        self.load_data()

    def load_data(self):
        """Loads room and reservation data from JSON, or initializes defaults."""
        if os.path.exists(self.data_file):
            with open(self.data_file, "r") as f:
                data = json.load(f)
                self.rooms = [Room.from_dict(r) for r in data.get("rooms", [])]
                self.reservations = [
                    Reservation.from_dict(b) for b in data.get("reservations", [])
                ]
        else:
            # Seed initial rooms if no file exists
            self.rooms = [
                Room(101, "Standard", 2500),
                Room(102, "Standard", 2500),
                Room(201, "Deluxe", 4500),
                Room(202, "Deluxe", 4500),
                Room(301, "Suite", 8500),
            ]
            self.save_data()

    def save_data(self):
        """Persists current state to the JSON file."""
        data = {
            "rooms": [r.to_dict() for r in self.rooms],
            "reservations": [b.to_dict() for b in self.reservations],
        }
        with open(self.data_file, "w") as f:
            json.dump(data, f, indent=4)

    def search_rooms(self, category=None):
        """Displays available rooms, optionally filtered by category."""
        print("\n--- Available Rooms ---")
        available = [
            r
            for r in self.rooms
            if r.is_available
            and (category is None or r.category.lower() == category.lower())
        ]

        if not available:
            print("No available rooms found matching your criteria.")
            return []

        print(f"{'Room No.':<10} {'Category':<15} {'Price/Night (₹)':<15}")
        print("-" * 42)
        for room in available:
            print(
                f"{room.room_number:<10} {room.category:<15} ₹{room.price_per_night:,.2f}"
            )
        return available

    def book_room(self):
        """Handles the end-to-end room reservation workflow."""
        print("\n--- Book a Room ---")
        cat_filter = input(
            "Filter by category (Standard / Deluxe / Suite) or press Enter for all: "
        ).strip()
        available = self.search_rooms(cat_filter if cat_filter else None)

        if not available:
            return

        try:
            room_num = int(input("\nEnter Room Number to book: "))
            nights = int(input("Enter number of nights: "))
            if nights <= 0:
                print("Number of nights must be at least 1.")
                return
        except ValueError:
            print("Invalid numeric input.")
            return

        selected_room = next(
            (r for r in available if r.room_number == room_num), None
        )
        if not selected_room:
            print("Selected room is either invalid or unavailable.")
            return

        guest_name = input("Enter Guest Full Name: ").strip()
        guest_phone = input("Enter Guest Phone Number: ").strip()

        total_amount = selected_room.price_per_night * nights
        print(
            f"\nBooking Summary: Room {selected_room.room_number} ({selected_room.category}) for {nights} night(s)."
        )

        # Simulate Payment
        success, txn_id = PaymentGateway.process_payment(total_amount)
        if not success:
            print("Reservation cancelled due to incomplete payment.")
            return

        # Finalize Booking
        booking_id = f"BKG-{uuid.uuid4().hex[:6].upper()}"
        selected_room.is_available = False

        new_reservation = Reservation(
            booking_id=booking_id,
            guest_name=guest_name,
            guest_phone=guest_phone,
            room_number=selected_room.room_number,
            category=selected_room.category,
            nights=nights,
            total_amount=total_amount,
            payment_status="Paid",
            transaction_id=txn_id,
        )

        self.reservations.append(new_reservation)
        self.save_data()
        print(f"\nReservation Confirmed! Your Booking ID is: {booking_id}")

    def view_booking_details(self):
        """Displays full details for a specific Booking ID."""
        booking_id = input("\nEnter Booking ID (e.g., BKG-XXXXXX): ").strip().upper()
        booking = next(
            (b for b in self.reservations if b.booking_id == booking_id), None
        )

        if not booking:
            print("No reservation found with that Booking ID.")
            return

        print("\n" + "=" * 40)
        print("           BOOKING DETAILS")
        print("=" * 40)
        print(f"Booking ID     : {booking.booking_id}")
        print(f"Status         : {booking.status}")
        print(f"Guest Name     : {booking.guest_name}")
        print(f"Phone          : {booking.guest_phone}")
        print(f"Room Number    : {booking.room_number} ({booking.category})")
        print(f"Duration       : {booking.nights} Night(s)")
        print(f"Total Paid     : ₹{booking.total_amount:,.2f}")
        print(f"Payment Status : {booking.payment_status} ({booking.transaction_id})")
        print(f"Booked On      : {booking.booked_at}")
        print("=" * 40)

    def cancel_reservation(self):
        """Cancels an active reservation and restores room availability."""
        booking_id = input("\nEnter Booking ID to cancel: ").strip().upper()
        booking = next(
            (b for b in self.reservations if b.booking_id == booking_id), None
        )

        if not booking:
            print("Booking ID not found.")
            return

        if booking.status == "Cancelled":
            print("This reservation is already cancelled.")
            return

        confirm = (
            input(
                f"Are you sure you want to cancel booking {booking_id} for {booking.guest_name}? (y/n): "
            )
            .strip()
            .lower()
        )
        if confirm == "y":
            booking.status = "Cancelled"
            booking.payment_status = "Refund Initiated"

            # Free up the room
            room = next(
                (r for r in self.rooms if r.room_number == booking.room_number), None
            )
            if room:
                room.is_available = True

            self.save_data()
            print(
                f"Reservation {booking_id} cancelled. Room {booking.room_number} is now available."
            )
            print(f"Refund of ₹{booking.total_amount:,.2f} has been initiated.")


def main():
    hotel = HotelSystem()

    while True:
        print("\n==========================================")
        print("        HOTEL RESERVATION SYSTEM")
        print("==========================================")
        print("1. Search Available Rooms")
        print("2. Book a Room")
        print("3. View Booking Details")
        print("4. Cancel Reservation")
        print("5. Exit")

        choice = input("\nSelect an option (1-5): ").strip()

        if choice == "1":
            cat = input(
                "Enter category (Standard / Deluxe / Suite) or press Enter for all: "
            ).strip()
            hotel.search_rooms(cat if cat else None)
        elif choice == "2":
            hotel.book_room()
        elif choice == "3":
            hotel.view_booking_details()
        elif choice == "4":
            hotel.cancel_reservation()
        elif choice == "5":
            print("Thank you for using the Hotel Reservation System. Goodbye!")
            break
        else:
            print("Invalid option. Please choose between 1 and 5.")


if __name__ == "__main__":
    main()