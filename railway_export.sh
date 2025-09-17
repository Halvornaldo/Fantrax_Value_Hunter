#!/bin/bash
# Railway Export Script - Optimized for Essential Tables Only
# Exports only the 7 tables verified to be used in production

echo "🚂 Starting Railway export..."
echo "📊 Exporting 7 essential tables (verified through code analysis)"

# Create timestamp for unique filename
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
FILENAME="railway_sync_${TIMESTAMP}.sql"

echo "📝 Creating export: $FILENAME"

# Set password for pg_dump (no prompting)
export PGPASSWORD=fantrax_password

# Export only essential tables (with connection parameters)
pg_dump \
  --host=localhost \
  --port=5433 \
  --username=fantrax_user \
  --dbname=fantrax_value_hunter \
  -t players \
  -t player_metrics \
  -t player_form \
  -t team_fixtures \
  -t fixture_odds \
  -t name_mappings \
  -t player_games_data \
  --no-owner \
  --no-privileges \
  --clean \
  --if-exists \
  > "$FILENAME"

# Check if export was successful
if [ $? -eq 0 ]; then
    echo "✅ Export successful!"
    echo "📁 File: $FILENAME"
    echo "📏 Size: $(du -h "$FILENAME" | cut -f1)"
    echo ""
    echo "📋 Exported tables:"
    echo "   • players (714 Premier League players)"
    echo "   • player_metrics (live performance stats)"
    echo "   • player_form (historical data for form calculations)"
    echo "   • team_fixtures (fixture difficulty scores)"
    echo "   • fixture_odds (betting odds for difficulty)"
    echo "   • name_mappings (global cross-source matching)"
    echo "   • player_games_data (games tracking for blending)"
    echo ""
    echo "🔗 Next step: Import to Railway with:"
    echo "   psql \$DATABASE_URL < $FILENAME"
else
    echo "❌ Export failed!"
    exit 1
fi