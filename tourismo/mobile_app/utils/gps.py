from plyer import gps

class GPSHelper:
    _started = False

    @staticmethod
    def get_location(cb_ok, cb_err):
        try:
            def on_location(**kw):
                lat, lon = kw.get("lat"), kw.get("lon")
                try:
                    gps.stop()
                except Exception:
                    pass
                GPSHelper._started = False
                cb_ok(float(lat), float(lon))

            def on_status(stype, status):
                # opcjonalnie: log statusu
                pass

            gps.configure(on_location=on_location, on_status=on_status)
            if not GPSHelper._started:
                gps.start(minTime=1000, minDistance=0)
                GPSHelper._started = True
        except Exception as e:
            cb_err(str(e))
