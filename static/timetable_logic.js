// --- AI Engine in JavaScript (to be run in a Web Worker) ---

let DAYS, TIME_SLOTS, all_classes_to_schedule;
let professors_df, rooms_df, subjects_df, student_groups_df;

// --- Core Genetic Algorithm Functions ---
function generateRandomTimetable() {
    let schedule = [];
    for (const load of all_classes_to_schedule) {
        const group = student_groups_df.find(g => g.group_id === load.group_id);
        const subject = subjects_df.find(s => s.subject_id === load.subject_id);
        const professor = professors_df.find(p => p.prof_id === load.prof_id);
        const day = DAYS[Math.floor(Math.random() * DAYS.length)];
        const time_slot = TIME_SLOTS[Math.floor(Math.random() * TIME_SLOTS.length)];
        const room = rooms_df[Math.floor(Math.random() * rooms_df.length)];
        schedule.push({ group, subject, professor, room, time_slot, day });
    }
    return { schedule, fitness: 0.0 };
}

function calculateFitness(timetable) {
    let clashes = 0;
    const occupied_slots = {};

    for (const cls of timetable.schedule) {
        const slot_key = `${cls.day}-${cls.time_slot}`;
        if (!occupied_slots[slot_key]) {
            occupied_slots[slot_key] = { professors: new Set(), groups: new Set(), rooms: new Set() };
        }
        const slot_info = occupied_slots[slot_key];
        if (slot_info.professors.has(cls.professor.prof_id)) clashes++;
        if (slot_info.groups.has(cls.group.group_id)) clashes++;
        if (slot_info.rooms.has(cls.room.room_id)) clashes++;
        slot_info.professors.add(cls.professor.prof_id);
        slot_info.groups.add(cls.group.group_id);
        slot_info.rooms.add(cls.room.room_id);
    }
    
    const daily_schedules = {};
    for (const cls of timetable.schedule) {
        const key = `${cls.group.group_id}-${cls.day}`;
        if (!daily_schedules[key]) daily_schedules[key] = [];
        daily_schedules[key].push(cls.time_slot);
    }

    let gap_penalties = 0;
    for (const key in daily_schedules) {
        const time_indices = daily_schedules[key].map(ts => TIME_SLOTS.indexOf(ts)).sort((a, b) => a - b);
        if (time_indices.length > 1) {
            const first = time_indices[0];
            const last = time_indices[time_indices.length - 1];
            const gaps = (last - first + 1) - time_indices.length;
            gap_penalties += gaps;
        }
    }
    
    return 1.0 / (1.0 + clashes + gap_penalties * 0.1);
}

function selectParent(population) {
    const tournament = [];
    for (let i = 0; i < 5; i++) {
        tournament.push(population[Math.floor(Math.random() * population.length)]);
    }
    return tournament.reduce((best, current) => (current.fitness > best.fitness) ? current : best);
}

function crossover(parent1, parent2) {
    const crossover_point = Math.floor(Math.random() * (parent1.schedule.length - 1)) + 1;
    const child_schedule = parent1.schedule.slice(0, crossover_point).concat(parent2.schedule.slice(crossover_point));
    return { schedule: child_schedule, fitness: 0.0 };
}

function mutate(timetable) {
    for (let i = 0; i < timetable.schedule.length; i++) {
        if (Math.random() < 0.05) {
            timetable.schedule[i].day = DAYS[Math.floor(Math.random() * DAYS.length)];
            timetable.schedule[i].time_slot = TIME_SLOTS[Math.floor(Math.random() * TIME_SLOTS.length)];
            timetable.schedule[i].room = rooms_df[Math.floor(Math.random() * rooms_df.length)];
        }
    }
    return timetable;
}

// --- Main Evolution Function ---
function runEvolution(params) {
    // Set up constants and data from the main thread
    DAYS = params.DAYS;
    TIME_SLOTS = params.TIME_SLOTS;
    professors_df = params.data.professors_df;
    rooms_df = params.data.rooms_df;
    subjects_df = params.data.subjects_df;
    student_groups_df = params.data.student_groups_df;

    all_classes_to_schedule = [];
    params.data.teaching_load_df.forEach(load => {
        const subject = subjects_df.find(s => s.subject_id === load.subject_id);
        if (subject) {
            for (let i = 0; i < subject.weekly_hours; i++) {
                all_classes_to_schedule.push(load);
            }
        }
    });

    let population = Array.from({ length: params.POPULATION_SIZE }, generateRandomTimetable);
    population.forEach(t => t.fitness = calculateFitness(t));
    
    for (let gen = 0; gen < params.NUM_GENERATIONS; gen++) {
        population.sort((a, b) => b.fitness - a.fitness);
        
        // Post progress update back to the main thread
        postMessage({ type: 'progress', generation: gen + 1, total: params.NUM_GENERATIONS, fitness: population[0].fitness });

        if (population[0].fitness > 0.999) break;

        const new_population = population.slice(0, params.ELITISM_SIZE);
        while (new_population.length < params.POPULATION_SIZE) {
            let child = mutate(crossover(selectParent(population), selectParent(population)));
            child.fitness = calculateFitness(child);
            new_population.push(child);
        }
        population = new_population;
    }
    
    // Post the final result back to the main thread
    postMessage({ type: 'result', timetable: population[0] });
}

// Listen for the 'start' message from the main thread
self.onmessage = function(e) {
    if (e.data.type === 'start') {
        runEvolution(e.data.params);
    }
};
