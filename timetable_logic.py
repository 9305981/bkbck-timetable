import pandas as pd
import random
from collections import defaultdict

# --- Data Structures (No changes needed here) ---
class ScheduledClass:
    def __init__(self, group, subject, professor, room, time_slot, day):
        self.group = group
        self.subject = subject
        self.professor = professor
        self.room = room
        self.time_slot = time_slot
        self.day = day
    def __repr__(self):
        return (f"[{self.day: <10} {self.time_slot: <12}] "
                f"Group: {self.group['group_name']} "
                f"Subject: {self.subject['subject_name']} "
                f"Prof: {self.professor['initials']} "
                f"Room: {self.room['room_name']}")
class Timetable:
    def __init__(self, schedule):
        self.schedule = schedule
        self.fitness = 0.0
    def __repr__(self):
        return f"Timetable with {len(self.schedule)} classes and fitness {self.fitness}"

# --- Helper functions (No changes needed here) ---
def get_group_color(group_id):
    colors = {
        'TYCS': '#FFDDC1', 'SYCS': '#C1DFFF', 'FYCS': '#DBC1FF',
        'MSCAI1': '#C1FFC1', 'MSC1': '#FFFAC1', 'SYDS': '#FFC1D8', 
        'FYDS': '#D6F8FF', 'MSC PART 2': '#FFC1E0'
    }
    return colors.get(group_id, '#E8E8E8')

def export_to_html(timetable, rooms, days, time_slots, filename="timetable.html"):
    # This function remains the same
    html = f"""<html><head><title>Master Timetable - BK BIRLA COLLEGE, KALYAN</title><style>
    body {{ font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; background-color: #f4f7f6; color: #333; margin: 20px; }}
    .header {{ text-align: center; margin-bottom: 30px; }}
    h1 {{ color: #0056b3; border-bottom: 2px solid #0056b3; padding-bottom: 10px; display: inline-block; }}
    h2 {{ text-align: center; color: #007bff; margin-top: 40px; margin-bottom: 20px; text-transform: uppercase; }}
    .table-container {{ overflow-x: auto; }}
    table {{ border-collapse: collapse; width: 100%; min-width: 1200px; margin: 0 auto 50px auto; box-shadow: 0 4px 8px rgba(0,0,0,0.1); background-color: #fff; }}
    th, td {{ border: 1px solid #c7d8e2; text-align: center; padding: 10px; vertical-align: middle; height: 60px; }}
    th {{ background-color: #e9f2f7; color: #333; font-weight: 600; }}
    .slot {{ font-weight: bold; color: #555; background-color: #e9f2f7; min-width: 120px;}}
    .cell-content {{ font-size: 0.8em; line-height: 1.4; font-weight: 500; padding: 4px; border-radius: 4px; }}
    .back-link {{ display: block; text-align: center; margin-bottom: 30px; font-size: 1.1em; color: #0056b3; text-decoration: none; font-weight: bold; }}
    .back-link:hover {{ text-decoration: underline; }}
    </style></head><body>
    <div class="header"><h1>BK BIRLA COLLEGE, KALYAN</h1></div>
    <a href="/" class="back-link">&larr; Back to Home Page</a>"""
    room_list = sorted(rooms['room_name'].tolist())
    for day in days:
        html += f"<h2>{day}</h2><div class='table-container'><table><tr><th>Time Slot</th>"
        for room_name in room_list:
            html += f"<th>{room_name}</th>"
        html += "</tr>"
        for time_slot in time_slots:
            html += f"<tr><td class='slot'>{time_slot}</td>"
            for room_name in room_list:
                scheduled_class = next((c for c in timetable.schedule if c.day == day and c.time_slot == time_slot and c.room['room_name'] == room_name), None)
                if scheduled_class:
                    bg_color = get_group_color(scheduled_class.group['group_id'])
                    html += f"<td style='background-color: {bg_color};'><div class='cell-content'>"
                    html += f"<b>{scheduled_class.subject['subject_name']}</b><br>({scheduled_class.group['group_id']})<br>{scheduled_class.professor['initials']}"
                    html += "</div></td>"
                else:
                    html += "<td></td>"
            html += "</tr>"
        html += "</table></div>"
    html += "</body></html>"
    with open(filename, "w") as f:
        f.write(html)
    print(f"\n✅ Timetable data exported to {filename}")

# --- Main AI Engine ---
def run_evolution(update_progress_callback, filename="timetable.html"):
    try:
        professors_df = pd.read_csv('professors.csv')
        rooms_df = pd.read_csv('rooms.csv')
        subjects_df = pd.read_csv('subjects.csv')
        student_groups_df = pd.read_csv('student_groups.csv')
        teaching_load_df = pd.read_csv('teaching_load.csv')
    except FileNotFoundError as e:
        update_progress_callback(0,0,0, error=f"Error: Could not find required file {e.filename}")
        return False

    DAYS = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday"]
    TIME_SLOTS = ["07:15-08:15", "08:15-09:15", "09:25-10:25", "10:25-11:25", "11:35-12:35", "12:35-13:35", "13:55-14:55", "14:55-15:55"]
    
    # ⭐ TUNED PARAMETERS FOR FASTER PERFORMANCE ⭐
    POPULATION_SIZE = 100
    NUM_GENERATIONS = 250 # Reduced generations
    MUTATION_RATE = 0.05 # Slightly increased mutation to explore more solutions
    TOURNAMENT_SIZE = 5
    ELITISM_SIZE = 10
    GAP_PENALTY = 0.1

    all_classes_to_schedule = []
    for _, load in teaching_load_df.iterrows():
        try:
            subject_hours = subjects_df.loc[subjects_df['subject_id'] == load['subject_id'], 'weekly_hours'].iloc[0]
            for _ in range(subject_hours):
                all_classes_to_schedule.append(load)
        except IndexError:
            update_progress_callback(0,0,0, error=f"Error: Subject '{load['subject_id']}' not found in subjects.csv.")
            return False

    def generate_random_timetable():
        schedule = []
        for load in all_classes_to_schedule:
            group = student_groups_df[student_groups_df['group_id'] == load['group_id']].iloc[0]
            subject = subjects_df[subjects_df['subject_id'] == load['subject_id']].iloc[0]
            professor = professors_df[professors_df['prof_id'] == load['prof_id']].iloc[0]
            schedule.append(ScheduledClass(group, subject, professor, rooms_df.sample(n=1).iloc[0], random.choice(TIME_SLOTS), random.choice(DAYS)))
        return Timetable(schedule)

    # ⭐ NEW, HYPER-OPTIMIZED FITNESS FUNCTION ⭐
    def calculate_fitness(timetable):
        clashes = 0
        occupied_slots = defaultdict(lambda: {'professors': set(), 'groups': set(), 'rooms': set()})
        
        for cls in timetable.schedule:
            slot_key = (cls.day, cls.time_slot)
            slot_info = occupied_slots[slot_key]

            # Check for hard clashes by attempting to add resources to the slot
            if cls.professor['prof_id'] in slot_info['professors']:
                clashes += 1
            slot_info['professors'].add(cls.professor['prof_id'])

            if cls.group['group_id'] in slot_info['groups']:
                clashes += 1
            slot_info['groups'].add(cls.group['group_id'])

            if cls.room['room_id'] in slot_info['rooms']:
                clashes += 1
            slot_info['rooms'].add(cls.room['room_id'])
            
        # Soft constraint for gaps (same as before)
        daily_schedules = defaultdict(list)
        for cls in timetable.schedule: daily_schedules[(cls.group['group_id'], cls.day)].append(cls.time_slot)
        gap_penalties = sum((max_ts - min_ts + 1) - len(time_indices)
                            for time_slots in daily_schedules.values()
                            if (time_indices := sorted([TIME_SLOTS.index(ts) for ts in time_slots]))
                            and (min_ts := time_indices[0]) is not None and (max_ts := time_indices[-1]) is not None)
        
        return 1.0 / (1.0 + clashes + gap_penalties * GAP_PENALTY)

    def select_parent(population):
        return max(random.sample(population, TOURNAMENT_SIZE), key=lambda t: t.fitness)

    def crossover(parent1, parent2):
        crossover_point = random.randint(1, len(parent1.schedule) - 1)
        return Timetable(parent1.schedule[:crossover_point] + parent2.schedule[crossover_point:])

    def mutate(timetable):
        for i in range(len(timetable.schedule)):
            if random.random() < MUTATION_RATE:
                timetable.schedule[i].day, timetable.schedule[i].time_slot, timetable.schedule[i].room = \
                    random.choice(DAYS), random.choice(TIME_SLOTS), rooms_df.sample(n=1).iloc[0]
        return timetable

    population = [generate_random_timetable() for _ in range(POPULATION_SIZE)]
    for timetable in population: timetable.fitness = calculate_fitness(timetable)
    
    for generation in range(NUM_GENERATIONS):
        population.sort(key=lambda x: x.fitness, reverse=True)
        update_progress_callback(generation + 1, NUM_GENERATIONS, population[0].fitness)
        if population[0].fitness > 0.999 and (1/population[0].fitness - 1) < 1:
            break
        new_population = population[:ELITISM_SIZE]
        while len(new_population) < POPULATION_SIZE:
            child = mutate(crossover(select_parent(population), select_parent(population)))
            child.fitness = calculate_fitness(child)
            new_population.append(child)
        population = new_population

    best_timetable = population[0]
    export_to_html(best_timetable, rooms_df, DAYS, TIME_SLOTS, filename)
    return True

# This block allows the script to be run directly for testing.
if __name__ == "__main__":
    print("Running timetable logic directly for testing...")
    def print_progress(gen, total_gen, fitness, error=None):
        if error:
            print(error)
            return
        print(f"Generation {gen}/{total_gen} | Best Fitness: {fitness:.4f}")
    
    run_evolution(print_progress)