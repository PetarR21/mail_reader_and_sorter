
        if not os.path.isfile("settings.json"):
            with open("settings.json", "w") as f:
                json.dump(
                    {"auto_sort_enabled": False, "auto_sort_interval_minutes": 10},
                    f,
                    indent=4,
                )
            return

        try:
            with open("settings.json", "r") as f:
                data = json.load(f)
                if not isinstance(data, dict):
                    raise ValueError("settings.json must contain a JSON dictionary")

                auto_sort_enabled = data.get("auto_sort_enabled", None)
                if isinstance(auto_sort_enabled, bool):
                    self.auto_sort_enabled = auto_sort_enabled

                auto_sort_interval_minutes = data.get(
                    "auto_sort_interval_minutes", None
                )

                if auto_sort_interval_minutes is not None:
                    try:
                        interval_value = int(auto_sort_interval_minutes)
                    except (TypeError, ValueError):
                        interval_value = None

                    if interval_value is not None and 1 <= interval_value <= 1440:
                        self.auto_sort_interval_minutes = interval_value

        except (json.JSONDecodeError, ValueError, FileNotFoundError):
            self.auto_sort_enabled = False
            self.auto_sort_interval_minutes = 10
            with open("settings.json", "w") as f:
                json.dump(
                    {
                        "auto_sort_enabled": self.auto_sort_enabled,
                        "auto_sort_interval_minutes": self.auto_sort_interval_minutes,
                    },
                    f,
                    indent=4,
                )

    def on_auto_sort_timeout(self):