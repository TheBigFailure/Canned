class OrderLineStatus:
    Pending = "P"                   # Pending confirmation (e.g. initial request made to server). Also known as "Created"
    Open = "O"                      # Open for changes
    Waiting_for_Balance = "W"       # A submitted payment without enough balance to pass on order to production
    Confirmed = "C"                 # Confirmed by the server
    In_Production = "I"             # Actively being made
    Delivered = "D"                 # Delivered to the user
    Returned = "R"                  # Returned by the user: return was successful
    Cancelled = "X"                 # Cancelled by the user
    Locked = "L"                    # Cannot be edited by those without access
    Standing_by_for_Stock = "S"     # Standing by for when stock is available

_ORDERLINESTATUSASDICT = dict({k: v for k, v in OrderLineStatus.__dict__.items() if not k.startswith("__")})

class LogType:
    Debug = "D"     # Debugging information
    Info = "I"      # Informational log
    Warning = "W"   # Warning log
    Error = "E"     # Error log
    Critical = "C"  # Critical error log

_LOGTYPEASDICT = dict({k: v for k, v in LogType.__dict__.items() if not k.startswith("__")})