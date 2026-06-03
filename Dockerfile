# Copyright (C) 2026 Tanguy Marsault - PhySense
# SPDX-License-Identifier: AGPL-3.0-or-later

FROM python:3.12-slim


RUN apt-get update && apt-get install -y --no-install-recommends \
    git

WORKDIR /app

COPY . .
RUN pip install -e .

EXPOSE 8000
CMD ["uvicorn", "physense_api.main:app", "--host", "0.0.0", "--port", "8000"]