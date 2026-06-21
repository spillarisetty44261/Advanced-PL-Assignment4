"""
Employee Shift Scheduler - Python
Advanced Programming Languages Assignment

Handles employee scheduling for a company that runs 7 days a week.
Shifts are morning, afternoon, and evening. Each employee picks
their preferred shifts and we try to honor that as much as possible.

I used a dictionary to store the schedule since it made the most
sense for looking things up by day and shift.
"""

import random


DAYS = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
SHIFTS = ["Morning", "Afternoon", "Evening"]

# business rules
MAX_DAYS_PER_WEEK = 5
MIN_EMPLOYEES_PER_SHIFT = 2


def collect_employee_data():
    """
    Asks the user to enter employees one by one.
    Also collects their shift preferences in order (bonus feature).
    Returns a list of dicts, one per employee.
    """
    employees = []

    print("\n" + "=" * 50)
    print("   Employee Shift Scheduler - Data Entry")
    print("=" * 50)
    print("Enter each employee and their shift preferences.")
    print("Type 'done' when you're finished.\n")

    while True:
        name = input("Employee name (or 'done'): ").strip()

        if name.lower() == "done":
            if len(employees) < 2:
                print("  Need at least 2 employees. Keep going!\n")
                continue
            break

        if not name:
            print("  Can't leave the name blank, try again.\n")
            continue

        # make sure we don't add the same person twice
        existing = [e["name"].lower() for e in employees]
        if name.lower() in existing:
            print(f"  '{name}' is already added.\n")
            continue

        # collect shift preferences - this is the bonus priority ranking part
        print(f"\n  Shift preferences for {name}:")
        print("  Options: Morning, Afternoon, Evening")
        print("  Enter from most to least preferred, comma separated.")
        print("  e.g.  Evening, Morning, Afternoon")

        raw = input("  Your order: ").strip()

        preferences = []
        valid = True
        for part in raw.split(","):
            shift = part.strip().capitalize()
            if shift not in SHIFTS:
                print(f"  '{shift}' isn't valid, going to randomize preferences.")
                valid = False
                break
            if shift not in preferences:
                preferences.append(shift)

        if not valid or len(preferences) == 0:
            preferences = SHIFTS[:]
            random.shuffle(preferences)
            print(f"  Randomized order: {', '.join(preferences)}")

        # fill in any shifts they didn't mention so we always have all 3
        for s in SHIFTS:
            if s not in preferences:
                preferences.append(s)

        emp = {
            "name": name,
            "preferences": preferences,
            "days_worked": 0,
            "assigned_days": set(),
            "shift_by_day": {}   # day -> shift name, so we can print it later
        }
        employees.append(emp)
        print(f"  Added {name}! Preference order: {' > '.join(preferences)}\n")

    return employees


def build_schedule(employees):
    """
    This is the main scheduling function. It runs in two stages:

    First it goes through every day and tries to assign each employee
    to their preferred shift. If they already have a shift that day or
    hit the 5 day limit, they get skipped or bumped to another shift.

    Then it checks if any shift has fewer than 2 people and randomly
    pulls in whoever is still available to fill the gap.
    """

    # build an empty schedule, nested dict by day then shift
    schedule = {}
    for day in DAYS:
        schedule[day] = {}
        for shift in SHIFTS:
            schedule[day][shift] = []

    # reset employee state in case this runs more than once
    for emp in employees:
        emp["days_worked"] = 0
        emp["assigned_days"] = set()
        emp["shift_by_day"] = {}

    # go through each day and assign employees based on preferences.
    # shuffling the day order so the same days don't always go last and
    # get starved once everyone hits their 5-day cap
    day_order = DAYS[:]
    random.shuffle(day_order)

    # cap how many people we place per day in this pass. without this,
    # the first few days processed soak up everyone's 5 days and the
    # last couple days end up with zero people left at all.
    # using the average capacity per day (rounded down a bit) leaves
    # pass 2 enough people in reserve to patch any shift that's short
    avg_per_day = (len(employees) * MAX_DAYS_PER_WEEK) // len(DAYS)
    max_per_day = max(MIN_EMPLOYEES_PER_SHIFT * len(SHIFTS), avg_per_day - 1)

    for day in day_order:
        # shuffle so the same people don't always get first pick
        todays_list = employees[:]
        random.shuffle(todays_list)

        placed_today = 0

        for emp in todays_list:
            if placed_today >= max_per_day:
                break  # leave the rest of today's slots for pass 2 / other days

            if emp["days_worked"] >= MAX_DAYS_PER_WEEK:
                continue  # already at 5 days, skip

            if day in emp["assigned_days"]:
                continue  # already working today somehow, skip

            placed = False

            # try each preference in order until one works
            for shift in emp["preferences"]:
                if try_assign(emp, day, shift, schedule):
                    placed = True
                    break

            # if none of the preferences worked try whatever's left
            # this probably won't happen often but just in case
            if not placed:
                for shift in SHIFTS:
                    if shift not in emp["preferences"]:
                        if try_assign(emp, day, shift, schedule):
                            placed = True
                            break

            if placed:
                placed_today += 1

    # now check if any shifts are understaffed and fill them in
    warnings = []
    for day in DAYS:
        for shift in SHIFTS:
            while len(schedule[day][shift]) < MIN_EMPLOYEES_PER_SHIFT:
                # find anyone who can still work today
                available = [
                    e for e in employees
                    if day not in e["assigned_days"] and e["days_worked"] < MAX_DAYS_PER_WEEK
                ]

                if not available:
                    warnings.append(f"Could not fill {shift} on {day} - not enough staff.")
                    break

                pick = random.choice(available)
                force_assign(pick, day, shift, schedule)

    return schedule, warnings


def try_assign(emp, day, shift, schedule):
    # returns False if there's a conflict (employee already has a shift today)
    if day in emp["assigned_days"]:
        return False

    schedule[day][shift].append(emp["name"])
    emp["assigned_days"].add(day)
    emp["shift_by_day"][day] = shift
    emp["days_worked"] += 1
    return True


def force_assign(emp, day, shift, schedule):
    # used when topping up understaffed shifts, no conflict check needed here
    schedule[day][shift].append(emp["name"])
    emp["assigned_days"].add(day)
    emp["shift_by_day"][day] = shift
    emp["days_worked"] += 1


def print_schedule(schedule, employees, warnings):
    """
    Prints the final schedule day by day, then shows
    how many days each employee ended up working.
    """
    print("\n" + "=" * 58)
    print("         FINAL WEEKLY EMPLOYEE SCHEDULE")
    print("=" * 58)

    for day in DAYS:
        print(f"\n  {day.upper()}")
        print("  " + "-" * 44)
        for shift in SHIFTS:
            names = schedule[day][shift]
            if names:
                print(f"    {shift:<13} {', '.join(names)}")
            else:
                print(f"    {shift:<13} (nobody assigned)")

    if warnings:
        print("\n  Warnings:")
        for w in warnings:
            print(f"    ! {w}")

    # summary of days worked per employee
    print("\n" + "=" * 58)
    print("  EMPLOYEE SUMMARY")
    print("  " + "-" * 44)
    for emp in employees:
        count = f"{emp['days_worked']}/{MAX_DAYS_PER_WEEK} days"
        print(f"    {emp['name']:<22} {count}")

    # shift order for each employee, day by day
    print("\n" + "=" * 58)
    print("  SHIFT ORDER BY EMPLOYEE")
    print("  " + "-" * 44)
    for emp in employees:
        print(f"\n    {emp['name']}:")
        worked_any = False
        for day in DAYS:
            if day in emp["shift_by_day"]:
                worked_any = True
                print(f"      {day:<11} {emp['shift_by_day'][day]}")
        if not worked_any:
            print("      (not scheduled this week)")

    print("\n" + "=" * 58 + "\n")


def main():
    print("\nWelcome to the Employee Shift Scheduler")

    employees = collect_employee_data()

    print("\nGenerating schedule...\n")
    schedule, warnings = build_schedule(employees)

    print_schedule(schedule, employees, warnings)


if __name__ == "__main__":
    main()