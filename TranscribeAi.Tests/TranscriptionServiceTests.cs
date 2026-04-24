using Moq;
using FluentAssertions;
using Xunit;
using TranscribeAi.Services.Implementations;
using TranscribeAi.Services.Interfaces;
using TranscribeAi.Services.DTOs;
using Microsoft.Extensions.Logging;

namespace TranscribeAi.Tests
{
    public class TranscriptionServiceTests
    {
        private readonly Mock<ITranscriptionProvider> _providerMock;
        private readonly Mock<ILogger<TranscriptionService>> _loggerMock;
        private readonly TranscriptionService _service;

        public TranscriptionServiceTests()
        {
            _providerMock = new Mock<ITranscriptionProvider>();
            _loggerMock = new Mock<ILogger<TranscriptionService>>();

            _service = new TranscriptionService(
                _providerMock.Object,
                _loggerMock.Object
            );
        }

        [Fact]
        public async Task TranscribeFileAsync_ShouldCallProvider_WhenInputIsValid()
        {
            // Arrange
            var filePath = "test.wav";
            var expectedResult = new TranscriptionResultDto 
            { 
                FullText = "Sample text", 
                DurationSeconds = 10,
                OverallConfidence = 0.95f,
                Segments = new List<SegmentDto>()
            };

            _providerMock.Setup(p => p.TranscribeAsync(filePath, null, It.IsAny<CancellationToken>()))
                         .ReturnsAsync(expectedResult);

            // Act
            var result = await _service.TranscribeFileAsync(filePath);

            // Assert
            Assert.NotNull(result);
            result.FullText.Should().Be("Sample text");
            _providerMock.Verify(p => p.TranscribeAsync(filePath, null, It.IsAny<CancellationToken>()), Times.Once);
        }
    }
}
