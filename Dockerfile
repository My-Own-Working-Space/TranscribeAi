# ──────────────────────────────────────────────────────────────────────
#  TranscribeAI — Production Dockerfile (ASP.NET Core 9)
# ──────────────────────────────────────────────────────────────────────

# Stage 1: Build
FROM mcr.microsoft.com/dotnet/sdk:9.0 AS build
WORKDIR /app

# Copy solution and projects for restore
COPY ["TranscribeAi.sln", "./"]
COPY ["TranscribeAi.Web/TranscribeAi.Web.csproj", "TranscribeAi.Web/"]
COPY ["TranscribeAi.Worker/TranscribeAi.Worker.csproj", "TranscribeAi.Worker/"]
COPY ["TranscribeAi.Services/TranscribeAi.Services.csproj", "TranscribeAi.Services/"]
COPY ["TranscribeAi.DataAccessLayer/TranscribeAi.DataAccessLayer.csproj", "TranscribeAi.DataAccessLayer/"]
COPY ["TranscribeAi.BusinessObject/TranscribeAi.BusinessObject.csproj", "TranscribeAi.BusinessObject/"]

# Restore dependencies
RUN dotnet restore "TranscribeAi.sln"

# Copy everything else and build
COPY . .
RUN dotnet publish "TranscribeAi.Web/TranscribeAi.Web.csproj" -c Release -o /app/out

# Stage 2: Runtime
FROM mcr.microsoft.com/dotnet/aspnet:9.0 AS runtime
WORKDIR /app
COPY --from=build /app/out .

# Environment variables
ENV ASPNETCORE_URLS=http://+:10000
ENV ASPNETCORE_ENVIRONMENT=Production

# Port exposed by Render (default is usually 10000)
EXPOSE 10000

# Start the application
ENTRYPOINT ["dotnet", "TranscribeAi.Web.dll"]
