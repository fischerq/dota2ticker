def check_field(message, field):
    if field not in message:
        print "{} is missing {}".format(message["Type"], field)
        return False
    else:
        return True


next_id = 0


def generate_id():
    #generate unique ID
    global next_id
    id_ = next_id
    next_id += 1
    return id_