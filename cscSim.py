import simpy
import random
import statistics

csc_statistics = {'waiting times':[], 'time till abandoned':[], 'call handling times': [], 'abandoned calls': 0, 'calls handled': 0, 'total calls': 0}
# CSC Stats NEEDED for accuracy
# -Time to deal with call in minutes
# -min/max time tenant will wait before abandoning calls
# -range of howmany calls per minute
# -average number of calls per day
# -average number of calls handled per day
# -average dropped calls per day


class Call_Centre(object):

    def __init__(self, env, num_staff):
        self.env = env
        self.staff = simpy.Resource(env, num_staff)

    def deal_with_query(self, tenant):
        call_answered_time = self.env.now

        print(f'dealing with tenant{tenant} [current_time: {call_answered_time: .2f}]')

        yield self.env.timeout(random.randint(1, 10)) # Time taken to deal with issue

        time_finished_query = self.env.now
        handle_time = time_finished_query - call_answered_time
        csc_statistics['call handling times'].append(handle_time)

        print(f'finished dealing with tenant{tenant} [current_time: {time_finished_query: .2f}]')
        print(f"Time taken to deal with Tenant{tenant}'s query: {handle_time: .2f}")

    def write_notes(self, staff):
        yield self.env.timeout(random.randint(1, 2))

    def lunch_break(self, staff):
        yield self.env.timeout(30)

def call_handle_process(env, tenant, call_center, minmax_patience):

    with call_center.staff.request() as request: # Requesting resource
        time_tenant_called = env.now
        patience = random.uniform(minmax_patience[0], minmax_patience[1]) # How long a tenant is willing to wait on the phone
        results = yield request | env.timeout(patience)
        csc_statistics['waiting times'].append(env.now - time_tenant_called)
        print(f'tenant{tenant} calling in...[current time: {time_tenant_called: .2f}]')

        if request in results: # If there is an available resource tenant will speak to call centre staff
            csc_statistics['calls handled'] += 1
            print(f'tenant{tenant} connection successful, dealing with query')
            yield env.process(call_center.deal_with_query(tenant))
        else: # If there are no staff when tenant patience has run out, tenant disconnects the call.
            time_tenant_dropped = env.now
            csc_statistics['abandoned calls'] += 1
            csc_statistics['time till abandoned'].append(time_tenant_dropped - time_tenant_called)
            print(f'tenant{tenant} dropped out of call queue [current time: {time_tenant_dropped: .2f}]')



def run_csc(env, num_staff, minmax_patience):
    minutes_between_calls = 0.69
    csc = Call_Centre(env, num_staff)
    waiting_in_que = 3  # Initial queue of tenants calling through
    call_count = 0

    print('Lines Open')
    # Running through initial queue
    for tenant in range(waiting_in_que):
        env.process(call_handle_process(env, tenant, csc, minmax_patience))
        call_count += 1

    while True: # This sections adds a new tenant to the queue every X amount of minutes
        yield env.timeout(random.uniform(0, 0.69))
        tenant += 1
        call_count += 1
        env.process(call_handle_process(env, tenant, csc, minmax_patience))
        csc_statistics['total calls'] = call_count

def calculate_handle_times(handle_time):
    average_handle = statistics.mean(handle_time)

    minutes, frac_minutes = divmod(average_handle, 1)
    seconds = frac_minutes * 60
    return round(minutes), round(seconds)

def calculate_wait_times(wait_times):
    average_wait = statistics.mean(wait_times)

    # Pretty print results:
    minutes, frac_minutes = divmod(average_wait, 1)
    seconds = frac_minutes * 60
    return round(minutes), round(seconds)

def calculate_abandoned_times(wait_times):
    try:
        average_wait = statistics.mean(wait_times)
        # Pretty print results:
        minutes, frac_minutes = divmod(average_wait, 1)
        seconds = frac_minutes * 60
    except Exception as e:
        minutes, seconds = 0, 0
    return round(minutes), round(seconds)

def main():
    # Variables
    min_max_patience = [1, 10]
    work_day_in_minutes = 540
    num_of_staff = 10
    random.seed(42)


    env = simpy.Environment()
    env.process(run_csc(env, num_of_staff, min_max_patience))
    env.run(until=work_day_in_minutes)
    drop_total = csc_statistics['abandoned calls']
    total_calls = csc_statistics['total calls']
    handled_calls = csc_statistics['calls handled']
    hmins, hsecs = calculate_handle_times(csc_statistics['call handling times'])
    wmins, wsecs = calculate_wait_times(csc_statistics['waiting times'])
    amins, asecs = calculate_abandoned_times(csc_statistics['time till abandoned'])
    print(f'\nNumber of Call Takers: {num_of_staff}'
          f'\nTotal Calls: {total_calls}'
          f'\nTotal Handled Calls: {handled_calls}'
          f'\nTotal Dropped Calls: {drop_total}'
          f'\nAverage Handle Time: {hmins} min(s) and {hsecs} sec(s)'
          f'\nAverage Wait Time: {wmins} min(s) and {wsecs} sec(s)'
          f'\nAverage Abandon Wait Time: {amins} min(s) and {asecs} sec(s)')

if __name__ == '__main__':
    main()