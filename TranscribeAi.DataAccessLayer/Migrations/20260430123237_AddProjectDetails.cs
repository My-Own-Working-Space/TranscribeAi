using Microsoft.EntityFrameworkCore.Migrations;

#nullable disable

namespace TranscribeAi.DataAccessLayer.Migrations
{
    /// <inheritdoc />
    public partial class AddProjectDetails : Migration
    {
        /// <inheritdoc />
        protected override void Up(MigrationBuilder migrationBuilder)
        {
            migrationBuilder.AddColumn<string>(
                name: "Description",
                table: "TranscriptionJobs",
                type: "character varying(2000)",
                maxLength: 2000,
                nullable: true);

            migrationBuilder.AddColumn<string>(
                name: "ProjectName",
                table: "TranscriptionJobs",
                type: "character varying(255)",
                maxLength: 255,
                nullable: true);
        }

        /// <inheritdoc />
        protected override void Down(MigrationBuilder migrationBuilder)
        {
            migrationBuilder.DropColumn(
                name: "Description",
                table: "TranscriptionJobs");

            migrationBuilder.DropColumn(
                name: "ProjectName",
                table: "TranscriptionJobs");
        }
    }
}
