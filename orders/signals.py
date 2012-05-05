from django.dispatch import Signal

pending_order_signal = Signal(providing_args=['call','order','user'])
confirmed_order_signal = Signal(providing_args=['order'])

