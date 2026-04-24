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
    public class ActionServiceTests
    {
        private readonly Mock<IUnitOfWork> _uowMock;
        private readonly Mock<ILlmService> _llmMock;
        private readonly Mock<ILogger<ActionService>> _loggerMock;
        private readonly ActionService _service;

        public ActionServiceTests()
        {
            _uowMock = new Mock<IUnitOfWork>();
            _llmMock = new Mock<ILlmService>();
            _loggerMock = new Mock<ILogger<ActionService>>();

            _service = new ActionService(
                _llmMock.Object,
                _uowMock.Object,
                _loggerMock.Object
            );
        }

        [Fact]
        public async Task ExtractActionsAsync_ShouldReturnEmpty_WhenNoTranscript()
        {
            // Arrange
            var jobId = Guid.NewGuid();
            var job = new TranscriptionJob { Id = jobId, Transcript = "" };

            _uowMock.Setup(u => u.TranscriptionJobs.GetByIdAsync(jobId, It.IsAny<CancellationToken>()))
                    .ReturnsAsync(job);

            // Act
            var result = await _service.ExtractActionsAsync(jobId);

            // Assert
            result.Should().BeEmpty();
        }

        [Fact]
        public async Task ExtractActionsAsync_ShouldSaveItems_WhenLlmReturnsData()
        {
            // Arrange
            var jobId = Guid.NewGuid();
            var job = new TranscriptionJob { Id = jobId, Transcript = "Need to call John tomorrow." };

            _uowMock.Setup(u => u.TranscriptionJobs.GetByIdAsync(jobId, It.IsAny<CancellationToken>()))
                    .ReturnsAsync(job);
            
            _uowMock.Setup(u => u.ActionItems.FindAsync(It.IsAny<Expression<Func<ActionItem, bool>>>(), It.IsAny<CancellationToken>()))
                    .ReturnsAsync(new List<ActionItem>());

            _llmMock.Setup(l => l.ChatAsync(It.IsAny<string>(), It.IsAny<string>(), It.IsAny<float>(), It.IsAny<int>(), It.IsAny<CancellationToken>()))
                    .ReturnsAsync("[{\"task\": \"Call John\", \"assignee\": \"Me\", \"priority\": \"high\"}]");
            
            _llmMock.Setup(l => l.ParseJsonResponse(It.IsAny<string>()))
                    .Returns(JsonDocument.Parse("[{\"task\": \"Call John\", \"assignee\": \"Me\", \"priority\": \"high\"}]"));

            // Act
            var result = await _service.ExtractActionsAsync(jobId);

            // Assert
            result.Should().HaveCount(1);
            result[0].TaskDescription.Should().Be("Call John");
            _uowMock.Verify(u => u.ActionItems.AddAsync(It.IsAny<ActionItem>(), It.IsAny<CancellationToken>()), Times.AtLeastOnce);
            _uowMock.Verify(u => u.SaveChangesAsync(It.IsAny<CancellationToken>()), Times.AtLeastOnce);
        }

        [Fact]
        public async Task UpdateActionAsync_ShouldModifyEntityAndSave()
        {
            // Arrange
            var actionId = Guid.NewGuid();
            var item = new ActionItem { Id = actionId, IsCompleted = false, Priority = "medium" };

            _uowMock.Setup(u => u.ActionItems.GetByIdAsync(actionId, It.IsAny<CancellationToken>()))
                    .ReturnsAsync(item);

            // Act
            var result = await _service.UpdateActionAsync(actionId, true, "high");

            // Assert
            result.IsCompleted.Should().BeTrue();
            result.Priority.Should().Be("high");
            _uowMock.Verify(u => u.ActionItems.Update(It.IsAny<ActionItem>()), Times.Once);
            _uowMock.Verify(u => u.SaveChangesAsync(It.IsAny<CancellationToken>()), Times.Once);
        }
    }
}
