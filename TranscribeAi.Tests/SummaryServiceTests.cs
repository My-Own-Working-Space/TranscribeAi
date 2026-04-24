using Moq;
using FluentAssertions;
using Xunit;
using TranscribeAi.Services.Implementations;
using TranscribeAi.Services.Interfaces;
using TranscribeAi.DataAccessLayer.Repositories.Interfaces;
using TranscribeAi.BusinessObject.Entities;
using TranscribeAi.BusinessObject.Enums;
using Microsoft.Extensions.Logging;
using System.Linq.Expressions;
using System.Text.Json;

namespace TranscribeAi.Tests
{
    public class SummaryServiceTests
    {
        private readonly Mock<IUnitOfWork> _uowMock;
        private readonly Mock<ILlmService> _llmMock;
        private readonly Mock<ILogger<SummaryService>> _loggerMock;
        private readonly SummaryService _service;

        public SummaryServiceTests()
        {
            _uowMock = new Mock<IUnitOfWork>();
            _llmMock = new Mock<ILlmService>();
            _loggerMock = new Mock<ILogger<SummaryService>>();

            _service = new SummaryService(
                _llmMock.Object,
                _uowMock.Object,
                _loggerMock.Object
            );
        }

        [Fact]
        public async Task GenerateSummaryAsync_ShouldThrow_WhenJobNotFound()
        {
            // Arrange
            _uowMock.Setup(u => u.TranscriptionJobs.GetByIdAsync(It.IsAny<Guid>(), It.IsAny<CancellationToken>()))
                    .ReturnsAsync((TranscriptionJob?)null);

            // Act & Assert
            await Assert.ThrowsAsync<InvalidOperationException>(() => 
                _service.GenerateSummaryAsync(Guid.NewGuid()));
        }

        [Fact]
        public async Task GenerateSummaryAsync_ShouldSucceed_AndSaveToDb()
        {
            // Arrange
            var jobId = Guid.NewGuid();
            var job = new TranscriptionJob 
            { 
                Id = jobId, 
                Transcript = "This is a meaningful transcript for a meeting.",
                Mode = JobMode.Meeting
            };

            _uowMock.Setup(u => u.TranscriptionJobs.GetByIdAsync(jobId, It.IsAny<CancellationToken>()))
                    .ReturnsAsync(job);
            
            _uowMock.Setup(u => u.Summaries.FindAsync(It.IsAny<Expression<Func<AISummary, bool>>>(), It.IsAny<CancellationToken>()))
                    .ReturnsAsync(new List<AISummary>());

            // Mock LLM generation
            var rawJson = "{\"summary\": \"Test Summary\", \"key_points\": [\"point1\"], \"conclusion\": \"Test Conclusion\"}";
            _llmMock.Setup(l => l.ChatAsync(It.IsAny<string>(), It.IsAny<string>(), It.IsAny<float>(), It.IsAny<int>(), It.IsAny<CancellationToken>()))
                    .ReturnsAsync(rawJson);
            
            _llmMock.Setup(l => l.ParseJsonResponse(rawJson))
                    .Returns(() => JsonDocument.Parse(rawJson));

            // Act
            var result = await _service.GenerateSummaryAsync(jobId);

            // Assert
            Assert.NotNull(result);
            result.Summary.Should().Be("Test Summary");
            _uowMock.Verify(u => u.Summaries.AddAsync(It.IsAny<AISummary>(), It.IsAny<CancellationToken>()), Times.Once);
            _uowMock.Verify(u => u.SaveChangesAsync(It.IsAny<CancellationToken>()), Times.AtLeastOnce);
        }
    }
}
